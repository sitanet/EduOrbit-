from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from backend.apps.eae.models import Question, QuestionChoice, Assessment, AssessmentAttempt, AttemptAnswer, AssessmentResult, ProctorLog
from backend.apps.core.services.notifications import UnifiedNotificationService

class QuestionBankService:
    """
    Question Bank Management & Item Versioning Engine.
    """
    @classmethod
    @transaction.atomic
    def create_question(cls, school, subject, text, question_type='mcq', choices_data=None):
        tenant = school.tenant

        question = Question.objects.create(
            tenant=tenant,
            school=school,
            subject=subject,
            topic="General",
            question_text=text,
            question_type=question_type,
            status='published'
        )

        if choices_data:
            for item in choices_data:
                QuestionChoice.objects.create(
                    tenant=tenant,
                    question=question,
                    choice_text=item.get('text', ''),
                    is_correct=item.get('is_correct', False)
                )

        return {
            "status": "success",
            "question_id": str(question.id),
            "question_text": question.question_text,
            "choices_count": question.choices.count()
        }


class ExaminationService:
    """
    CBT Exam Builder & Scheduling Engine.
    """
    @classmethod
    @transaction.atomic
    def create_exam(cls, school, title, duration_minutes=60):
        tenant = school.tenant

        exam = Assessment.objects.create(
            tenant=tenant,
            school=school,
            title=title,
            duration_minutes=duration_minutes,
            is_active=True
        )

        return {
            "status": "success",
            "exam_id": str(exam.id),
            "title": exam.title,
            "duration_minutes": exam.duration_minutes
        }


class CandidateService:
    """
    CBT Candidate Session Registration & Secure Browser Engine.
    """
    @classmethod
    @transaction.atomic
    def start_exam(cls, student, assessment):
        tenant = student.tenant

        attempt, _ = AssessmentAttempt.objects.get_or_create(
            tenant=tenant,
            student=student,
            assessment=assessment,
            defaults={'status': 'started', 'time_started': timezone.now()}
        )

        # Log proctor security session initialization
        ProctorLog.objects.create(
            tenant=tenant,
            attempt=attempt,
            event_type="session_start",
            metadata={"device": "Secure CBT Browser"}
        )

        return {
            "status": "success",
            "attempt_id": str(attempt.id),
            "student_number": student.student_number,
            "exam_title": assessment.title,
            "duration_minutes": assessment.duration_minutes,
            "time_started": str(attempt.time_started)
        }


class AutoMarkingService:
    """
    Instant Auto-Grading & Scoring Engine.
    """
    @classmethod
    @transaction.atomic
    def auto_grade_attempt(cls, attempt):
        answers = attempt.answers.all()
        total_earned = Decimal('0.00')
        total_questions = answers.count() or 1

        for ans in answers:
            if ans.selected_choice and ans.selected_choice.is_correct:
                ans.is_correct = True
                ans.marks_earned = Decimal('1.00')
            else:
                ans.is_correct = False
                ans.marks_earned = Decimal('0.00')
            ans.save()
            total_earned += ans.marks_earned

        percentage = (total_earned / Decimal(str(total_questions))) * Decimal('100.00')
        attempt.status = 'completed'
        attempt.time_submitted = timezone.now()
        attempt.save()

        # Cache Assessment Result
        result, _ = AssessmentResult.objects.get_or_create(
            tenant=attempt.tenant,
            student=attempt.student,
            assessment=attempt.assessment,
            defaults={'total_score': total_earned, 'percentage': percentage, 'grade': 'A' if percentage >= 70 else 'B'}
        )
        result.total_score = total_earned
        result.percentage = percentage
        result.grade = 'A' if percentage >= 70 else ('B' if percentage >= 50 else 'F')
        result.save()

        return {
            "status": "success",
            "attempt_id": str(attempt.id),
            "total_score": float(total_earned),
            "percentage": float(percentage),
            "grade": result.grade
        }


class ResultService:
    """
    Exam Results Publishing & Parent Notification Engine.
    """
    @classmethod
    @transaction.atomic
    def publish_results(cls, assessment):
        results = AssessmentResult.objects.filter(assessment=assessment)

        for res in results:
            # Send Notification Alert to Parent/Student
            UnifiedNotificationService.send_notification(
                recipient=res.student.person.first_name,
                title="CBT Exam Result Published",
                message=f"Results for '{assessment.title}' published: {res.percentage}% (Grade: {res.grade}).",
                channels=['in_app', 'email']
            )

        return {
            "status": "success",
            "assessment_title": assessment.title,
            "published_count": results.count()
        }
