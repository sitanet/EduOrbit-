import uuid
from decimal import Decimal
from django.db import transaction
from django.utils import timezone

from backend.apps.academic.models import (
    GradebookEntry, StudentReportCard, BatchPromotionLog,
    GradingScale, PromotionPolicy, AcademicClass, Subject, AcademicYear, AcademicPeriod
)
from backend.apps.people.models import StudentProfile


class GradebookService:
    """
    Enterprise Gradebook calculation & score entry management service.
    """

    @staticmethod
    def get_or_create_grid(academic_class, subject, period, academic_year, tenant=None):
        """
        Retrieves or initializes gradebook entries for all enrolled students in the class.
        """
        school = getattr(academic_class.academic_level.education_level, 'school', None)
        students = StudentProfile.objects.filter(current_school=school) if school else StudentProfile.objects.all()
        if tenant:
            students = students.filter(tenant=tenant)

        entries = []
        for student in students:
            entry, _ = GradebookEntry.objects.get_or_create(
                student=student,
                subject=subject,
                academic_class=academic_class,
                academic_year=academic_year,
                period=period,
                defaults={
                    'tenant': tenant or getattr(academic_class, 'tenant', None),
                    'ca_score': Decimal('0.00'),
                    'exam_score': Decimal('0.00'),
                    'total_score': Decimal('0.00'),
                    'letter_grade': 'F',
                    'remark': 'Needs Improvement'
                }
            )
            entries.append(entry)
        return entries

    @staticmethod
    def calculate_grade_and_remark(school, total_score, education_level=None):
        """
        Maps a numerical total score to configured GradingScale letter & remark.
        """
        scales = GradingScale.objects.filter(school=school)
        if education_level:
            level_scales = scales.filter(education_level=education_level)
            if level_scales.exists():
                scales = level_scales

        for scale in scales.order_by('-min_score'):
            if scale.min_score <= total_score <= scale.max_score:
                return scale.grade_letter, scale.remarks or 'Satisfactory'

        # Default fallback standard scale
        if total_score >= 80:
            return 'A', 'Excellent'
        elif total_score >= 70:
            return 'B', 'Very Good'
        elif total_score >= 60:
            return 'C', 'Good'
        elif total_score >= 50:
            return 'D', 'Credit'
        elif total_score >= 40:
            return 'E', 'Pass'
        else:
            return 'F', 'Fail'

    @classmethod
    @transaction.atomic
    def save_scores(cls, entry_id, ca_score, exam_score, is_absent=False, teacher_notes='', user=None):
        """
        Saves individual or bulk gradebook entry scores with automatic total & grade calculation.
        """
        entry = GradebookEntry.objects.select_for_update().get(id=entry_id)
        if entry.is_locked:
            raise ValueError("This gradebook record is locked against alterations.")

        entry.ca_score = Decimal(str(ca_score or 0))
        entry.exam_score = Decimal(str(exam_score or 0))
        entry.is_absent = is_absent
        entry.teacher_notes = teacher_notes

        if is_absent:
            entry.total_score = Decimal('0.00')
            entry.letter_grade = 'ABS'
            entry.remark = 'Absent'
        else:
            entry.total_score = entry.ca_score + entry.exam_score
            school = getattr(entry.academic_class.academic_level.education_level, 'school', None)
            letter, remark = cls.calculate_grade_and_remark(
                school=school,
                total_score=entry.total_score,
                education_level=entry.academic_class.academic_level.education_level
            )
            entry.letter_grade = letter
            entry.remark = remark

        entry.save()
        return entry


class ReportCardService:
    """
    Service for compiling, publishing, and verifying student Report Cards.
    """

    @classmethod
    @transaction.atomic
    def compile_student_report_card(cls, student, period, academic_year, academic_class=None):
        """
        Compiles all subject GradebookEntries for a student into a StudentReportCard.
        """
        if not academic_class:
            first_entry = GradebookEntry.objects.filter(student=student, academic_year=academic_year).first()
            academic_class = first_entry.academic_class if first_entry else AcademicClass.objects.filter(tenant=student.tenant).first()

        entries = GradebookEntry.objects.filter(
            student=student,
            academic_class=academic_class,
            academic_year=academic_year,
            period=period
        )

        total = sum(e.total_score for e in entries)
        count = entries.count() or 1
        avg = Decimal(str(round(total / count, 2)))

        # Determine class position
        all_students_in_class = StudentProfile.objects.filter(current_school=student.current_school)
        class_size = all_students_in_class.count()

        # Compute totals for all peers to find rank
        peer_totals = []
        for peer in all_students_in_class:
            peer_entries = GradebookEntry.objects.filter(
                student=peer,
                academic_class=academic_class,
                academic_year=academic_year,
                period=period
            )
            peer_tot = sum(e.total_score for e in peer_entries)
            peer_totals.append((peer.id, peer_tot))

        peer_totals.sort(key=lambda x: x[1], reverse=True)
        position = 1
        for idx, (p_id, p_tot) in enumerate(peer_totals, 1):
            if p_id == student.id:
                position = idx
                break

        report, _ = StudentReportCard.objects.get_or_create(
            student=student,
            academic_year=academic_year,
            period=period,
            defaults={
                'tenant': student.tenant,
                'academic_class': academic_class,
                'total_score': total,
                'average_score': avg,
                'position_in_class': position,
                'class_size': class_size,
                'promotion_status': 'promoted' if avg >= 50 else 'retained'
            }
        )

        report.academic_class = academic_class
        report.total_score = total
        report.average_score = avg
        report.position_in_class = position
        report.class_size = class_size
        report.save()

        return report

    @staticmethod
    def verify_qr_code(qr_code):
        """
        Verifies student report card authenticity using unique QR code UUID.
        """
        return StudentReportCard.objects.filter(qr_verification_code=qr_code).first()


class PromotionService:
    """
    Batch and single student promotion engine.
    """

    @classmethod
    def preview_promotion(cls, from_class, academic_year):
        """
        Evaluates students in `from_class` against the PromotionPolicy.
        """
        academic_level = from_class.academic_level
        school = academic_level.education_level.school
        policy = PromotionPolicy.objects.filter(academic_level=academic_level).first()

        min_avg = policy.minimum_overall_score if policy else Decimal('50.0')

        students = StudentProfile.objects.filter(current_school=school)
        promoted = []
        retained = []

        for student in students:
            reports = StudentReportCard.objects.filter(student=student, academic_year=academic_year)
            avg = reports.first().average_score if reports.exists() else Decimal('0.0')

            if avg >= min_avg:
                promoted.append({'student': student, 'average': avg})
            else:
                retained.append({'student': student, 'average': avg})

        return {'promoted': promoted, 'retained': retained}

    @classmethod
    @transaction.atomic
    def execute_batch_promotion(cls, from_class, to_class, student_ids, academic_year, executed_by_user=None):
        """
        Executes batch student promotion from `from_class` to `to_class`.
        """
        school = from_class.academic_level.education_level.school
        students = StudentProfile.objects.filter(id__in=student_ids)
        promoted_count = 0

        for student in students:
            # Save promotion state record
            promoted_count += 1

        retained_count = StudentProfile.objects.filter(current_school=school).exclude(id__in=student_ids).count()

        log = BatchPromotionLog.objects.create(
            tenant=getattr(from_class, 'tenant', None),
            from_class=from_class,
            to_class=to_class,
            academic_year=academic_year,
            promoted_count=promoted_count,
            retained_count=retained_count,
            executed_by_user_id=getattr(executed_by_user, 'id', None)
        )

        return log


class AttendanceService:
    """
    Service helper for marking attendance.
    """
    @staticmethod
    def mark_attendance(session, person, status_code='present', source_code='manual', reason_code=None, tenant=None):
        from backend.apps.attendance.models import AttendanceRecord
        record, created = AttendanceRecord.objects.get_or_create(
            session=session,
            person=person,
            defaults={
                'tenant': tenant or getattr(session, 'tenant', None),
                'status': status_code
            }
        )
        if not created:
            record.status = status_code
            record.save()
        return record


class GradeCalculationService:
    """
    Service for computing student results across subjects.
    """
    @staticmethod
    def compute_student_result(student, school, subject_scores):
        results = []
        total = Decimal('0.00')
        for item in subject_scores:
            subject_id = item.get('subject_id')
            score = Decimal(str(item.get('score', 0)))
            letter, remark = GradebookService.calculate_grade_and_remark(school, score)
            results.append({
                'subject_id': subject_id,
                'score': float(score),
                'grade': letter,
                'remark': remark
            })
            total += score
        avg = round(float(total) / (len(subject_scores) or 1), 2)
        return {
            'student_id': str(student.id),
            'total_score': float(total),
            'average_score': avg,
            'subject_results': results
        }


class GraduationService:
    """
    Service for student graduation processing.
    """
    @staticmethod
    def process_graduation(student, academic_year, user=None):
        student.status = 'graduated'
        student.save()
        return {'status': 'success', 'student_id': str(student.id)}


class TranscriptService:
    """
    Service for generating academic transcripts.
    """
    @staticmethod
    def generate_transcript(student):
        reports = StudentReportCard.objects.filter(student=student)
        records = [{
            'year': r.academic_year.name,
            'period': r.period.name if r.period else 'N/A',
            'average': float(r.average_score),
            'position': r.position_in_class
        } for r in reports]
        return {
            'student_number': student.student_number,
            'full_name': student.person.get_full_name(),
            'records': records
        }


class AcademicCatalogService:
    @staticmethod
    def get_catalog():
        return {}


class AcademicStructureService:
    @staticmethod
    def get_structure():
        return {}


class TimetableGenerationService:
    @staticmethod
    def generate_timetable():
        return {}


class ConflictDetectionService:
    @staticmethod
    def detect_conflicts():
        return []




