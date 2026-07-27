import uuid
from django.db import models
from django.utils import timezone
from backend.apps.core.models import TenantBaseModel

class EmployeeAsset(TenantBaseModel):
    employee = models.ForeignKey('hr.EmployeeProfile', on_delete=models.CASCADE, related_name='assigned_assets')
    asset_name = models.CharField(max_length=150)
    serial_number = models.CharField(max_length=100, blank=True)
    asset_type = models.CharField(max_length=50, default='IT Equipment')
    date_assigned = models.DateField(default=timezone.now)
    date_returned = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.asset_name} ({self.serial_number}) - {self.employee.employee_number}"
