from django.db import models
from django.utils import timezone
from backend.apps.core.models import TenantBaseModel

class CompensationHistory(TenantBaseModel):
    """
    Effective-dated salary compensation versioning.
    Never overwrites historical salary rates.
    """
    employee = models.ForeignKey('hr.EmployeeProfile', on_delete=models.CASCADE, related_name='compensation_history')
    effective_start_date = models.DateField(default=timezone.now)
    effective_end_date = models.DateField(null=True, blank=True)
    base_salary = models.DecimalField(max_digits=12, decimal_places=2)
    currency_code = models.CharField(max_length=10, default='NGN')
    salary_grade = models.CharField(max_length=50, default='grade_1')
    change_reason = models.CharField(max_length=200, blank=True)
    is_current = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.employee.employee_number}: {self.currency_code} {self.base_salary} ({self.effective_start_date})"


class ContractHistory(TenantBaseModel):
    """
    Immutable tracking of contract lifecycle changes (Probation -> Permanent -> Renewal).
    """
    employee = models.ForeignKey('hr.EmployeeProfile', on_delete=models.CASCADE, related_name='contract_history')
    contract_type = models.CharField(max_length=50)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.employee.employee_number}: {self.contract_type} ({self.start_date})"
