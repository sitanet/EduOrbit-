from django.db import models
from backend.apps.core.models import TenantBaseModel

class ApprovalWorkflow(TenantBaseModel):
    """
    Dynamic Workflow Designer Model.
    Configurable approval chains (e.g. Request -> HOD -> Dean -> Principal -> HR -> Payroll).
    """
    WORKFLOW_TYPES = [
        ('leave', 'Leave Approval Workflow'),
        ('attendance_adjustment', 'Attendance Adjustment Workflow'),
        ('recruitment', 'Recruitment Hiring Workflow'),
        ('promotion', 'Promotion Workflow'),
        ('transfer', 'Employee Transfer Workflow'),
        ('salary_increment', 'Salary Increment Workflow'),
        ('exit', 'Offboarding Exit Workflow'),
    ]
    name = models.CharField(max_length=150)
    workflow_type = models.CharField(max_length=50, choices=WORKFLOW_TYPES)
    steps_config = models.JSONField(default=list, help_text="List of approval step objects: [{'step': 1, 'role': 'hod'}, {'step': 2, 'role': 'principal'}]")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.get_workflow_type_display()})"
