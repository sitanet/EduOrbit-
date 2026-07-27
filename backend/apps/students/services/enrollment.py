from django.db import transaction
from django.utils import timezone
from backend.apps.people.models import StudentProfile
from backend.apps.students.models import (
    StudentStatusHistory, AcademicPlacementHistory, ClassPromotion, StudentTransfer
)
from backend.apps.students.services.student_number import StudentNumberGeneratorService
from backend.apps.core.services.notifications import UnifiedNotificationService

class EnrollmentService:
    """
    Comprehensive Enrollment & Student Records Engine.
    Handles New Enrollment, Promotions, Withdrawals, Transfers, and Re-enrollment.
    """
    @classmethod
    @transaction.atomic
    def enroll_student(cls, person, school, academic_year, academic_class, enrollment_type='new', house=None):
        tenant = school.tenant
        
        # 1. Generate or retrieve student number
        student_number = StudentNumberGeneratorService.generate_next_student_number(tenant=tenant)
        admission_number = f"ADM-{student_number.split('-')[-1]}"

        # 2. Get or create StudentProfile
        student_profile, created = StudentProfile.objects.get_or_create(
            person=person,
            tenant=tenant,
            defaults={
                'student_number': student_number,
                'admission_number': admission_number,
                'current_school': school,
                'enrollment_status': 'active'
            }
        )
        if not created and student_profile.enrollment_status != 'active':
            student_profile.enrollment_status = 'active'
            student_profile.save()

        # 3. Create Placement History
        placement = AcademicPlacementHistory.objects.create(
            tenant=tenant,
            student=student_profile,
            academic_year=academic_year,
            academic_class=academic_class,
            house=house,
            campus=school.campuses.first() if hasattr(school, 'campuses') else None
        )

        # 4. Status History Log
        status_log = StudentStatusHistory.objects.create(
            tenant=tenant,
            student=student_profile,
            status='active',
            reason=f"Enrollment ({enrollment_type.upper()}) into {academic_class.name}"
        )

        # 5. Send Notification
        UnifiedNotificationService.send_notification(
            recipient=person.first_name,
            title="Enrollment Complete",
            message=f"Enrollment ({enrollment_type}) confirmed in {academic_class.name}. Student ID: {student_profile.student_number}.",
            channels=['in_app', 'email']
        )

        return {
            "status": "success",
            "enrollment_type": enrollment_type,
            "student_profile_id": str(student_profile.id),
            "student_number": student_profile.student_number,
            "placement_id": str(placement.id),
            "status_log_id": str(status_log.id)
        }

    @classmethod
    @transaction.atomic
    def promote_student(cls, student_profile, previous_class, new_class, reason="Automatic Year End Promotion"):
        tenant = student_profile.tenant

        promotion = ClassPromotion.objects.create(
            tenant=tenant,
            student=student_profile,
            previous_class=previous_class,
            new_class=new_class,
            reason=reason
        )

        return {
            "status": "success",
            "student_number": student_profile.student_number,
            "previous_class": previous_class.name,
            "new_class": new_class.name,
            "promotion_id": str(promotion.id)
        }

    @classmethod
    @transaction.atomic
    def withdraw_student(cls, student_profile, reason="Parent Relocation"):
        tenant = student_profile.tenant

        student_profile.enrollment_status = 'withdrawn'
        student_profile.save()

        status_log = StudentStatusHistory.objects.create(
            tenant=tenant,
            student=student_profile,
            status='withdrawn',
            reason=reason
        )

        return {
            "status": "success",
            "student_number": student_profile.student_number,
            "new_status": "withdrawn",
            "status_log_id": str(status_log.id)
        }

    @classmethod
    @transaction.atomic
    def transfer_student(cls, student_profile, previous_school, new_school, reason="Campus Transfer"):
        tenant = student_profile.tenant

        student_profile.current_school = new_school
        student_profile.save()

        transfer = StudentTransfer.objects.create(
            tenant=tenant,
            student=student_profile,
            previous_school=previous_school,
            new_school=new_school,
            reason=reason
        )

        return {
            "status": "success",
            "student_number": student_profile.student_number,
            "new_school": new_school.name,
            "transfer_id": str(transfer.id)
        }
