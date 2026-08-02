from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from backend.apps.tenants.models import Tenant, School
from backend.apps.people.models import Person, StudentProfile
from backend.apps.academic.models import (
    Curriculum, AcademicYear, AcademicPeriod, EducationLevel,
    AcademicLevel, AcademicClass, Subject, GradebookEntry,
    StudentReportCard, BatchPromotionLog
)
from backend.apps.academic.services import GradebookService, ReportCardService, PromotionService


class AcademicEnterpriseCompletionTests(TestCase):
    """
    Unit tests for Enterprise Gradebook, Report Cards, and Student Promotion workflows.
    """

    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Tenant")
        self.school = School.objects.create(tenant=self.tenant, name="Academy High")
        
        self.year = AcademicYear.objects.create(
            tenant=self.tenant,
            school=self.school,
            name="2026/2027",
            code="2026-2027",
            start_date=timezone.now().date(),
            end_date=(timezone.now() + timedelta(days=365)).date(),
            status="active"
        )
        self.period = AcademicPeriod.objects.create(
            tenant=self.tenant,
            academic_year=self.year,
            name="Term 1",
            order=1,
            start_date=timezone.now().date(),
            end_date=(timezone.now() + timedelta(days=90)).date(),
            status="active"
        )
        self.edu_level = EducationLevel.objects.create(
            tenant=self.tenant,
            school=self.school,
            name="Secondary",
            code="secondary"
        )
        self.acad_level = AcademicLevel.objects.create(
            tenant=self.tenant,
            education_level=self.edu_level,
            name="JSS 1",
            code="jss-1"
        )
        self.class_from = AcademicClass.objects.create(
            tenant=self.tenant,
            academic_level=self.acad_level,
            name="JSS 1 Gold"
        )
        self.class_to = AcademicClass.objects.create(
            tenant=self.tenant,
            academic_level=self.acad_level,
            name="JSS 2 Gold"
        )
        self.curriculum = Curriculum.objects.create(
            name="National Curriculum",
            code="nat-curr"
        )
        self.subject = Subject.objects.create(
            tenant=self.tenant,
            school=self.school,
            curriculum=self.curriculum,
            name="Mathematics",
            code="MATH101"
        )
        
        self.person = Person.objects.create(
            tenant=self.tenant,
            person_number="PERS-TEST-001",
            date_of_birth=timezone.now().date(),
            first_name="Jane",
            last_name="Doe"
        )
        self.student = StudentProfile.objects.create(
            tenant=self.tenant,
            person=self.person,
            current_school=self.school,
            student_number="STD-001"
        )

    def test_gradebook_save_scores_calculates_total_and_grade(self):
        grid = GradebookService.get_or_create_grid(
            academic_class=self.class_from,
            subject=self.subject,
            period=self.period,
            academic_year=self.year,
            tenant=self.tenant
        )
        self.assertEqual(len(grid), 1)
        entry = grid[0]

        updated = GradebookService.save_scores(
            entry_id=entry.id,
            ca_score=35,
            exam_score=50,
            is_absent=False,
            teacher_notes="Great performance"
        )
        self.assertEqual(updated.total_score, Decimal('85.00'))
        self.assertEqual(updated.letter_grade, 'A')
        self.assertEqual(updated.remark, 'Excellent')

    def test_report_card_compilation_and_qr_verification(self):
        # Create gradebook entry
        grid = GradebookService.get_or_create_grid(
            academic_class=self.class_from,
            subject=self.subject,
            period=self.period,
            academic_year=self.year,
            tenant=self.tenant
        )
        GradebookService.save_scores(entry_id=grid[0].id, ca_score=30, exam_score=40)

        report = ReportCardService.compile_student_report_card(
            student=self.student,
            period=self.period,
            academic_year=self.year
        )
        self.assertEqual(report.total_score, Decimal('70.00'))
        self.assertEqual(report.position_in_class, 1)

        verified = ReportCardService.verify_qr_code(report.qr_verification_code)
        self.assertIsNotNone(verified)
        self.assertEqual(verified.id, report.id)

    def test_batch_promotion_execution(self):
        log = PromotionService.execute_batch_promotion(
            from_class=self.class_from,
            to_class=self.class_to,
            student_ids=[self.student.id],
            academic_year=self.year
        )
        self.assertEqual(log.promoted_count, 1)
