import uuid
from django.db import models
from backend.apps.core.models import TenantBaseModel

class HRSettings(TenantBaseModel):
    """
    SaaS Tenant-specific HR configurations and sub-module feature licensing flags.
    """
    payroll_frequency = models.CharField(max_length=30, default='monthly')
    pension_employee_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=8.00)
    pension_employer_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)
    paye_tax_formula = models.CharField(max_length=50, default='statutory_graduated')
    leave_accrual_policy = models.CharField(max_length=50, default='annual_upfront')
    working_hours_per_day = models.IntegerField(default=8)
    overtime_hourly_multiplier = models.DecimalField(max_digits=4, decimal_places=2, default=1.50)
    weekend_days = models.JSONField(default=list, blank=True)  # [5, 6]
    employee_number_prefix = models.CharField(max_length=20, default='EMP')
    probation_duration_months = models.IntegerField(default=6)
    retirement_age_years = models.IntegerField(default=60)
    
    # Sub-Module Feature Flags
    enable_recruitment = models.BooleanField(default=True)
    enable_payroll = models.BooleanField(default=True)
    enable_performance = models.BooleanField(default=True)
    enable_training = models.BooleanField(default=True)
    enable_assets = models.BooleanField(default=True)
    enable_ess = models.BooleanField(default=True)

    def __str__(self):
        return f"HR Settings - {self.tenant.name}"
