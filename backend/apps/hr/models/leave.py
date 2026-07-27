import uuid
from django.db import models
from django.utils import timezone
from backend.apps.core.models import TenantBaseModel
from backend.apps.hr.constants import LEAVE_STATUS

class LeaveType(TenantBaseModel):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=30)
    default_days_per_year = models.IntegerField(default=20)
    is_paid = models.BooleanField(default=True)
    requires_document = models.BooleanField(default=False)
    allow_encashment = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.code})"


class LeavePolicy(TenantBaseModel):
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE, related_name='policies')
    salary_grade = models.CharField(max_length=50, default='all')
    allowed_days = models.IntegerField(default=20)
    accrual_frequency = models.CharField(max_length=30, default='annual')

    def __str__(self):
        return f"Policy: {self.leave_type.name} - Grade: {self.salary_grade}"


class LeaveRequest(TenantBaseModel):
    employee = models.ForeignKey('hr.EmployeeProfile', on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.SET_NULL, null=True, blank=True)
    leave_type_name = models.CharField(max_length=100, default='Annual Leave')
    start_date = models.DateField()
    end_date = models.DateField()
    days_requested = models.IntegerField(default=1)
    status = models.CharField(max_length=30, choices=LEAVE_STATUS, default='draft')
    reason = models.TextField(blank=True)
    attachment_url = models.CharField(max_length=255, blank=True)
    workflow_instance = models.ForeignKey('workflow.WorkflowInstance', on_delete=models.SET_NULL, null=True, blank=True)
    supervisor_approved_at = models.DateTimeField(null=True, blank=True)
    hr_approved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.employee.employee_number}: {self.leave_type_name} ({self.days_requested} days - {self.status})"


class LeaveBalance(TenantBaseModel):
    employee = models.ForeignKey('hr.EmployeeProfile', on_delete=models.CASCADE, related_name='leave_balances')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.SET_NULL, null=True, blank=True)
    leave_type_name = models.CharField(max_length=100, default='Annual Leave')
    allowed_days = models.IntegerField(default=20)
    used_days = models.IntegerField(default=0)
    remaining_days = models.IntegerField(default=20)
    year = models.IntegerField(default=2026)

    def __str__(self):
        return f"{self.employee.employee_number}: {self.leave_type_name} ({self.remaining_days}/{self.allowed_days})"


class PublicHoliday(TenantBaseModel):
    name = models.CharField(max_length=150)
    holiday_name = models.CharField(max_length=150, null=True, blank=True)
    date = models.DateField()
    is_recurring = models.BooleanField(default=True)
    recurring = models.BooleanField(default=True)
    active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if self.holiday_name:
            self.name = self.holiday_name
        else:
            self.holiday_name = self.name
        self.is_recurring = self.recurring
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name or self.holiday_name} - {self.date}"


class LeaveEncashment(TenantBaseModel):
    employee = models.ForeignKey('hr.EmployeeProfile', on_delete=models.CASCADE, related_name='encashments')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    days_to_encash = models.IntegerField(default=1)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    status = models.CharField(max_length=30, default='submitted')  # submitted, approved, paid, rejected
    approved_by = models.ForeignKey('hr.EmployeeProfile', on_delete=models.SET_NULL, null=True, blank=True, related_name='encashments_approved')

    def __str__(self):
        return f"Encashment: {self.employee.employee_number} ({self.days_to_encash} days - {self.amount})"
