from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from backend.apps.lms.models import (
    LearningModule, LearningUnit, LearningActivity, StudentProgress,
    Course, CourseCategory, CourseLesson, Quiz, QuizQuestion, QuizAttempt
)
from backend.apps.core.services.notifications import UnifiedNotificationService

class CourseService:
    """
    LMS Course, Module & Unit Authoring Engine.
    """
    @classmethod
    @transaction.atomic
    def create_course(cls, school, subject, title, category=None, description=""):
        tenant = school.tenant

        course = Course.objects.create(
            tenant=tenant,
            school=school,
            subject=subject,
            category=category,
            title=title,
            description=description,
            is_published=True
        )

        return {
            "status": "success",
            "course_id": str(course.id),
            "title": course.title,
            "subject_name": subject.name,
            "is_published": course.is_published
        }

    @classmethod
    @transaction.atomic
    def create_module(cls, school, subject, title, topic="General"):
        tenant = school.tenant

        module = LearningModule.objects.create(
            tenant=tenant,
            school=school,
            subject=subject,
            title=title,
            topic=topic,
            version=1
        )

        return {
            "status": "success",
            "module_id": str(module.id),
            "title": module.title,
            "subject_name": subject.name,
            "topic": module.topic
        }

    @classmethod
    @transaction.atomic
    def add_unit(cls, module, name, order=1):
        unit = LearningUnit.objects.create(
            tenant=module.tenant,
            module=module,
            name=name,
            order=order
        )

        return {
            "status": "success",
            "unit_id": str(unit.id),
            "module_title": module.title,
            "unit_name": unit.name,
            "order": unit.order
        }


class LessonService:
    """
    Interactive Lesson Planning & Digital Media Delivery Engine.
    """
    @classmethod
    @transaction.atomic
    def create_lesson(cls, course, title, content_body="", video_url="", order=1):
        tenant = course.tenant

        lesson = CourseLesson.objects.create(
            tenant=tenant,
            course=course,
            title=title,
            content_body=content_body,
            video_url=video_url,
            order=order,
            is_published=True
        )

        return {
            "status": "success",
            "lesson_id": str(lesson.id),
            "course_title": course.title,
            "title": lesson.title,
            "order": lesson.order
        }


class QuizService:
    """
    Question Bank, Auto-Grading & Exam Analytics Engine.
    """
    @classmethod
    @transaction.atomic
    def create_quiz(cls, course, title, total_marks=100, pass_marks=50):
        tenant = course.tenant

        quiz = Quiz.objects.create(
            tenant=tenant,
            course=course,
            title=title,
            total_marks=total_marks,
            pass_marks=pass_marks
        )

        return {
            "status": "success",
            "quiz_id": str(quiz.id),
            "course_title": course.title,
            "title": quiz.title,
            "total_marks": quiz.total_marks
        }

    @classmethod
    @transaction.atomic
    def submit_quiz(cls, quiz, student, score_achieved):
        tenant = student.tenant
        score = Decimal(str(score_achieved))
        is_pass = score >= Decimal(str(quiz.pass_marks))

        attempt = QuizAttempt.objects.create(
            tenant=tenant,
            quiz=quiz,
            student=student,
            score_achieved=score,
            is_passed=is_pass,
            submitted_at=timezone.now()
        )

        # Alert Student
        UnifiedNotificationService.send_notification(
            recipient=student.person.first_name,
            title="Quiz Result Available",
            message=f"You scored {score}/{quiz.total_marks} on Quiz '{quiz.title}'. Status: {'PASSED' if is_pass else 'FAILED'}.",
            channels=['in_app', 'email']
        )

        return {
            "status": "success",
            "attempt_id": str(attempt.id),
            "quiz_title": quiz.title,
            "student_number": student.student_number,
            "score": float(score),
            "is_passed": is_pass
        }


class AssignmentSubmissionService:
    """
    Student Assignment Submissions & Activity Tracking Engine.
    """
    @classmethod
    @transaction.atomic
    def submit_assignment(cls, student, activity, content_body=""):
        tenant = student.tenant

        progress, _ = StudentProgress.objects.get_or_create(
            tenant=tenant,
            student=student,
            activity=activity,
            defaults={
                'status': 'completed',
                'completion_percentage': Decimal('100.00'),
                'last_access': timezone.now()
            }
        )

        progress.status = 'completed'
        progress.completion_percentage = Decimal('100.00')
        progress.last_access = timezone.now()
        progress.save()

        # Notify Teacher
        UnifiedNotificationService.send_notification(
            recipient="Subject Teacher",
            title="Assignment Submitted",
            message=f"Student {student.student_number} submitted assignment '{activity.name}'.",
            channels=['in_app', 'email']
        )

        return {
            "status": "success",
            "progress_id": str(progress.id),
            "student_number": student.student_number,
            "activity_name": activity.name,
            "submission_status": progress.status
        }


class GradeSubmissionService:
    """
    Online Grading & Performance Publishing Engine.
    """
    @classmethod
    @transaction.atomic
    def grade_submission(cls, progress, score_percentage):
        score = Decimal(str(score_percentage))
        progress.completion_percentage = score
        progress.save()

        # Notify Student / Parent
        UnifiedNotificationService.send_notification(
            recipient=progress.student.person.first_name,
            title="Assignment Graded",
            message=f"Your submission for '{progress.activity.name}' was graded: {score}%.",
            channels=['in_app', 'email']
        )

        return {
            "status": "success",
            "student_number": progress.student.student_number,
            "activity_name": progress.activity.name,
            "score": float(score)
        }
