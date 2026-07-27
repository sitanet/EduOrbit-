import uuid
from django.db import models
from django.utils import timezone
from backend.apps.core.models import TenantBaseModel

class PerformanceReview(TenantBaseModel):
    employee = models.ForeignKey('hr.EmployeeProfile', on_delete=models.CASCADE, related_name='appraisals')
    reviewer = models.ForeignKey('hr.EmployeeProfile', on_delete=models.CASCADE, related_name='appraisals_conducted')
    score = models.DecimalField(max_digits=5, decimal_places=2)
    review_date = models.DateField(default=timezone.now)
    remarks = models.TextField(blank=True)

    def __str__(self):
        return f"Review: {self.employee.employee_number} Score: {self.score}"


class PerformanceObjective(TenantBaseModel):
    employee = models.ForeignKey('hr.EmployeeProfile', on_delete=models.CASCADE, related_name='objectives')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    target_date = models.DateField()
    progress_percentage = models.IntegerField(default=0)
    status = models.CharField(max_length=30, default='not_started')

    def __str__(self):
        return f"{self.title} ({self.progress_percentage}%) - {self.employee.employee_number}"
