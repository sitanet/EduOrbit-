from django.db import transaction
from backend.apps.people.models import Person, TeacherProfile
from backend.apps.hr.models import EmployeeProfile, CompensationHistory
from backend.apps.core.services.notifications import UnifiedNotificationService

class HRMSSISIntegrationService:
    """
    Cross-Module Decoupled Integration Service linking HRMS and SIS domains.
    Handles Employee -> Teacher mapping, substitute teacher leave assignment, and teaching workload allowances.
    """
    @classmethod
    @transaction.atomic
    def map_employee_to_teacher(cls, employee_profile, teaching_license_number=""):
        person = employee_profile.person
        teacher_profile, created = TeacherProfile.objects.get_or_create(
            person=person,
            tenant=employee_profile.tenant,
            defaults={
                'employee_number': employee_profile.employee_number,
                'teaching_license_number': teaching_license_number
            }
        )
        if not created and teaching_license_number:
            teacher_profile.teaching_license_number = teaching_license_number
            teacher_profile.save()

        return {
            "status": "success",
            "is_created": created,
            "employee_number": employee_profile.employee_number,
            "teacher_profile_id": str(teacher_profile.id)
        }

    @classmethod
    def assign_substitute_teacher(cls, leave_request, substitute_teacher_person):
        """
        Triggers substitute teacher coverage when a primary teacher is on approved leave.
        """
        original_teacher = leave_request.employee.person
        
        # Notify Substitute Teacher
        UnifiedNotificationService.send_notification(
            recipient=substitute_teacher_person.first_name,
            title="Substitute Teacher Assignment",
            message=f"You have been assigned as substitute teacher for {original_teacher.first_name} {original_teacher.last_name} during approved leave.",
            channels=['in_app', 'email']
        )

        return {
            "status": "success",
            "leave_request_id": str(leave_request.id),
            "original_teacher": f"{original_teacher.first_name} {original_teacher.last_name}",
            "substitute_teacher": f"{substitute_teacher_person.first_name} {substitute_teacher_person.last_name}"
        }

    @classmethod
    def calculate_teaching_allowance(cls, employee_profile, assigned_class_count):
        """
        Calculates extra teaching workload allowance for HR Payroll processing.
        Base: ₦15,000 per extra class arm above 3 assigned classes.
        """
        extra_classes = max(0, assigned_class_count - 3)
        allowance_amount = extra_classes * 15000.00
        
        return {
            "employee_number": employee_profile.employee_number,
            "assigned_class_count": assigned_class_count,
            "extra_classes": extra_classes,
            "teaching_allowance": allowance_amount
        }
