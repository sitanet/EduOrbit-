import uuid
from django.db import models
from backend.apps.core.models import TenantBaseModel

class PayrollPeriod(TenantBaseModel):
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=30, default='draft') # draft, calculated, pending_approval, approved, posted, posting_failed, paid, reversed

    def __str__(self):
        return self.name


class PayrollGLAccount(TenantBaseModel):
    """
    GL Account mappings for payroll postings.
    """
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=150)

    def __str__(self):
        return f"{self.code} - {self.name}"


class SalaryStructure(TenantBaseModel):
    grade = models.CharField(max_length=50, unique=True)
    base_salary = models.DecimalField(max_digits=12, decimal_places=2)
    housing_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    transport_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    other_allowances = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    tax_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    pension_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    net_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.grade}: {self.base_salary}"


class PayrollAccountingConfiguration(TenantBaseModel):
    """
    Mandatory General Ledger account mappings for payroll postings.
    """
    salary_expense_account = models.ForeignKey(PayrollGLAccount, on_delete=models.PROTECT, related_name='salary_expense_configs')
    paye_liability_account = models.ForeignKey(PayrollGLAccount, on_delete=models.PROTECT, related_name='paye_liability_configs')
    pension_liability_account = models.ForeignKey(PayrollGLAccount, on_delete=models.PROTECT, related_name='pension_liability_configs')
    net_salary_liability_account = models.ForeignKey(PayrollGLAccount, on_delete=models.PROTECT, related_name='net_salary_liability_configs')
    
    # Additional Statutory and organization-specific accounts
    nhf_liability_account = models.ForeignKey(PayrollGLAccount, on_delete=models.PROTECT, null=True, blank=True, related_name='nhf_liability_configs')
    nsitf_liability_account = models.ForeignKey(PayrollGLAccount, on_delete=models.PROTECT, null=True, blank=True, related_name='nsitf_liability_configs')
    itf_liability_account = models.ForeignKey(PayrollGLAccount, on_delete=models.PROTECT, null=True, blank=True, related_name='itf_liability_configs')
    gratuity_provision_account = models.ForeignKey(PayrollGLAccount, on_delete=models.PROTECT, null=True, blank=True, related_name='gratuity_provision_configs')
    leave_accrual_account = models.ForeignKey(PayrollGLAccount, on_delete=models.PROTECT, null=True, blank=True, related_name='leave_accrual_configs')
    overtime_expense_account = models.ForeignKey(PayrollGLAccount, on_delete=models.PROTECT, null=True, blank=True, related_name='overtime_expense_configs')
    bonus_expense_account = models.ForeignKey(PayrollGLAccount, on_delete=models.PROTECT, null=True, blank=True, related_name='bonus_expense_configs')

    def __str__(self):
        return f"Payroll GL Mapping - {self.tenant.name}"


class PayrollRun(TenantBaseModel):
    period = models.ForeignKey(PayrollPeriod, on_delete=models.CASCADE)
    total_gross = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_tax = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_pension = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_net = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    status = models.CharField(max_length=30, default='draft') # draft, calculated, pending_approval, approved, posted, posting_failed, paid, reversed
    
    # Versioning metadata
    calculation_version = models.CharField(max_length=30, default='V1')
    tax_rules_version = models.CharField(max_length=30, default='V1')
    pension_rules_version = models.CharField(max_length=30, default='V1')
    minimum_wage_version = models.CharField(max_length=30, default='V1')

    def __str__(self):
        return f"Payroll Run {self.id} for {self.period.name} ({self.status})"


class PayrollPayslip(TenantBaseModel):
    payroll_run = models.ForeignKey(PayrollRun, on_delete=models.CASCADE, related_name='payslips')
    employee = models.ForeignKey('hr.EmployeeProfile', on_delete=models.CASCADE, related_name='payslips')
    gross_pay = models.DecimalField(max_digits=12, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2)
    pension_amount = models.DecimalField(max_digits=12, decimal_places=2)
    net_pay = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=30, default='draft')

    # Snapshot fields for auditability
    base_salary = models.DecimalField(max_digits=12, decimal_places=2)
    housing_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    transport_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    other_allowances = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    pension_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    nhf_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    nhf_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    currency = models.CharField(max_length=10, default='NGN')
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=4, default=1.0000)
    salary_grade = models.CharField(max_length=50)
    employment_type = models.CharField(max_length=50, default='full_time')
    
    tax_rule_version = models.CharField(max_length=30, default='V1')
    pension_rule_version = models.CharField(max_length=30, default='V1')
    nhf_rule_version = models.CharField(max_length=30, default='V1')
    calculation_version = models.CharField(max_length=30, default='V1')

    # Attendance Snapshot fields
    working_days = models.IntegerField(default=0)
    paid_days = models.IntegerField(default=0)
    absent_days = models.IntegerField(default=0)
    leave_days = models.IntegerField(default=0)
    holiday_days = models.IntegerField(default=0)
    weekend_days = models.IntegerField(default=0)
    late_minutes = models.IntegerField(default=0)
    overtime_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    night_shift_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    public_holiday_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    approved_adjustment_count = models.IntegerField(default=0)

    def __str__(self):
        return f"Payslip: {self.employee.employee_number} - Net: {self.net_pay}"
