from django.db import transaction
from backend.apps.people.models import StudentProfile
from backend.apps.students.models import StudentStatusHistory, STUDENT_LIFECYCLE_TRANSITIONS

class StudentLifecycleService:
    """
    Manages Student Lifecycle Transitions and historical audit logging.
    Transitions: pending -> active -> suspended -> withdrawn -> graduated -> alumni -> archived.
    """
    @classmethod
    @transaction.atomic
    def transition_student_status(cls, student_profile, new_status, reason="", performed_by=None):
        current_status = getattr(student_profile, 'enrollment_status', 'pending')
        allowed = STUDENT_LIFECYCLE_TRANSITIONS.get(current_status, [])

        if new_status not in allowed and current_status != new_status:
            raise ValueError(f"Invalid transition from '{current_status}' to '{new_status}'. Allowed: {allowed}")

        student_profile.enrollment_status = new_status
        student_profile.save()

        history = StudentStatusHistory.objects.create(
            tenant=student_profile.tenant,
            student=student_profile,
            status=new_status,
            reason=reason
        )

        return {
            "status": "success",
            "student_number": student_profile.student_number,
            "previous_status": current_status,
            "new_status": new_status,
            "history_id": str(history.id)
        }
