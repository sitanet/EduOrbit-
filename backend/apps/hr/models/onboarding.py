import uuid
from django.db import models
from backend.apps.core.models import TenantBaseModel
from backend.apps.hr.constants import ONBOARDING_CATEGORY

class OnboardingChecklist(TenantBaseModel):
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class OnboardingTask(TenantBaseModel):
    employee = models.ForeignKey('hr.EmployeeProfile', on_delete=models.CASCADE, related_name='onboarding_tasks')
    task_name = models.CharField(max_length=150)
    category = models.CharField(max_length=50, choices=ONBOARDING_CATEGORY, default='contract')
    due_date = models.DateField()
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey('hr.EmployeeProfile', on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks_verified')

    def __str__(self):
        return f"{self.task_name} - {self.employee.employee_number} ({'Done' if self.is_completed else 'Pending'})"
