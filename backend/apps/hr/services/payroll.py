from decimal import Decimal
from dataclasses import dataclass
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from backend.apps.hr.models.payroll import (
    PayrollPeriod, SalaryStructure, PayrollRun, PayrollPayslip, 
    PayrollAccountingConfiguration, PayrollGLAccount
)
from backend.apps.hr.models.employee import EmployeeProfile
from backend.apps.hr.models.settings import HRSettings
from backend.apps.core.services.outbox import OutboxService
from backend.apps.core.domain_events import DomainEvents
from backend.apps.core.interfaces import AccountingPostingInterface, PayrollPostingCommand, PayrollPostingLine

@dataclass(frozen=True)
class PayrollResult:
    base_salary: Decimal
    housing_allowance: Decimal
    transport_allowance: Decimal
    other_allowances: Decimal
    gross_pay: Decimal
    tax_amount: Decimal
    pension_amount: Decimal
    nhf_amount: Decimal
    net_pay: Decimal
    calculation_version: str = "V1"

class PayrollCalculationEngineV1:
    @staticmethod
    def calculate(base_salary, housing_allowance=0, transport_allowance=0, other_allowances=0, pension_rate=8.00, tax_formula='statutory_graduated'):
        base_salary = Decimal(str(base_salary))
        housing_allowance = Decimal(str(housing_allowance))
        transport_allowance = Decimal(str(transport_allowance))
        other_allowances = Decimal(str(other_allowances))
        
        gross_pay = base_salary + housing_allowance + transport_allowance + other_allowances
        
        # Pension: rate% of basic salary
        pension_amount = base_salary * (Decimal(str(pension_rate)) / Decimal('100.00'))
        
        # NHF: 2.5% of basic salary
        nhf_amount = base_salary * Decimal('0.025')
        
        # Tax calculation
        if tax_formula == 'statutory_graduated':
            taxable_income = gross_pay - pension_amount - nhf_amount
            if taxable_income < 0:
                taxable_income = Decimal('0.00')
            
            tax_amount = Decimal('0.00')
            if taxable_income <= 50000:
                tax_amount = taxable_income * Decimal('0.05')
            elif taxable_income <= 150000:
                tax_amount = (Decimal('50000') * Decimal('0.05')) + ((taxable_income - Decimal('50000')) * Decimal('0.10'))
            else:
                tax_amount = (Decimal('50000') * Decimal('0.05')) + (Decimal('100000') * Decimal('0.10')) + ((taxable_income - Decimal('150000')) * Decimal('0.15'))
        else:
            tax_amount = gross_pay * Decimal('0.10')
            
        net_pay = gross_pay - tax_amount - pension_amount - nhf_amount
        
        return PayrollResult(
            base_salary=base_salary,
            housing_allowance=housing_allowance,
            transport_allowance=transport_allowance,
            other_allowances=other_allowances,
            gross_pay=gross_pay.quantize(Decimal('0.01')),
            tax_amount=tax_amount.quantize(Decimal('0.01')),
            pension_amount=pension_amount.quantize(Decimal('0.01')),
            nhf_amount=nhf_amount.quantize(Decimal('0.01')),
            net_pay=net_pay.quantize(Decimal('0.01'))
        )

class PayrollService:
    @staticmethod
    @transaction.atomic
    def generate_payroll_run(tenant, period_id):
        # 1. Validate period exists and is not closed/calculated
        period = PayrollPeriod.objects.select_for_update().get(id=period_id, tenant=tenant)
        if period.status in ['closed', 'calculated', 'approved']:
            raise ValidationError(f"Payroll period is already in {period.status} status.")

        # 2. Validate Accounting Configuration presence before calculation
        config = PayrollAccountingConfiguration.objects.filter(tenant=tenant).first()
        if not config:
            raise ValidationError("Payroll configuration incomplete. Missing GL account mappings.")
        if not config.nhf_liability_account:
            raise ValidationError("Payroll configuration incomplete. Missing NHF liability account mapping.")
        
        # 3. Retrieve settings
        settings = HRSettings.objects.filter(tenant=tenant).first()
        pension_rate = settings.pension_employee_percentage if settings else Decimal('8.00')
        tax_formula = settings.paye_tax_formula if settings else 'statutory_graduated'

        # 4. Fetch all active employees
        employees = EmployeeProfile.objects.filter(tenant=tenant, is_deleted=False)
        if not employees.exists():
            raise ValidationError("No active employees found to generate payroll.")

        # 5. Create the PayrollRun header
        run = PayrollRun.objects.create(
            tenant=tenant,
            period=period,
            status='draft'
        )

        total_gross = Decimal('0.00')
        total_tax = Decimal('0.00')
        total_pension = Decimal('0.00')
        total_net = Decimal('0.00')

        # Chunk process employees (default size 500)
        chunk_size = 500
        emp_list = list(employees)
        for i in range(0, len(emp_list), chunk_size):
            chunk = emp_list[i:i + chunk_size]
            for emp in chunk:
                # Find salary structure for grade
                structure = SalaryStructure.objects.filter(tenant=tenant, grade=emp.salary_grade).first()
                if not structure:
                    # Skip or log error if no structure defined
                    continue
                
                # Perform stateless V1 calculations
                res = PayrollCalculationEngineV1.calculate(
                    base_salary=structure.base_salary,
                    housing_allowance=structure.housing_allowance,
                    transport_allowance=structure.transport_allowance,
                    other_allowances=structure.other_allowances,
                    pension_rate=pension_rate,
                    tax_formula=tax_formula
                )

                # Retrieve attendance summary snapshot
                from backend.apps.hr.selectors.attendance import AttendanceSelector
                summary = AttendanceSelector.get_payroll_attendance_summary(emp, period.start_date, period.end_date)

                # Save snapshot to payslip
                PayrollPayslip.objects.create(
                    tenant=tenant,
                    payroll_run=run,
                    employee=emp,
                    gross_pay=res.gross_pay,
                    tax_amount=res.tax_amount,
                    pension_amount=res.pension_amount,
                    net_pay=res.net_pay,
                    status='draft',
                    
                    base_salary=res.base_salary,
                    housing_allowance=res.housing_allowance,
                    transport_allowance=res.transport_allowance,
                    other_allowances=res.other_allowances,
                    tax_rate=Decimal('10.00') if tax_formula != 'statutory_graduated' else Decimal('0.00'),
                    pension_rate=pension_rate,
                    nhf_rate=Decimal('2.50'),
                    nhf_amount=res.nhf_amount,
                    salary_grade=emp.salary_grade,
                    employment_type='full_time',
                    
                    working_days=summary.working_days,
                    paid_days=summary.paid_days,
                    absent_days=summary.absent_days,
                    leave_days=summary.leave_days,
                    holiday_days=summary.holiday_days,
                    weekend_days=summary.weekend_days,
                    late_minutes=summary.late_minutes,
                    overtime_hours=summary.overtime_hours,
                    night_shift_hours=summary.night_shift_hours,
                    public_holiday_hours=summary.public_holiday_hours,
                    approved_adjustment_count=summary.approved_adjustment_count
                )

                total_gross += res.gross_pay
                total_tax += res.tax_amount
                total_pension += res.pension_amount
                total_net += res.net_pay

        # Update run header aggregates
        run.total_gross = total_gross
        run.total_tax = total_tax
        run.total_pension = total_pension
        run.total_net = total_net
        run.status = 'calculated'
        run.save()

        period.status = 'calculated'
        period.save()

        # Record outbox event on commit
        OutboxService.record_event(
            tenant=tenant,
            event_name=DomainEvents.PAYROLL_GENERATED,
            aggregate_type="PayrollRun",
            aggregate_id=str(run.id),
            payload={
                "payroll_run_id": str(run.id),
                "period_id": str(period.id),
                "total_net": str(total_net)
            }
        )

        return run

    @staticmethod
    def approve_and_post_payroll(tenant, run_id, accounting_service: AccountingPostingInterface):
        try:
            with transaction.atomic():
                run = PayrollRun.objects.select_for_update().get(id=run_id, tenant=tenant)
                if run.status != 'calculated':
                    raise ValidationError(f"Cannot approve payroll in status: {run.status}")

                run.status = 'approved'
                run.save()

                # Retrieve GL Mapping configuration
                config = PayrollAccountingConfiguration.objects.get(tenant=tenant)

                # Build posting lines
                lines = [
                    PayrollPostingLine(account_name=config.salary_expense_account.name, amount=run.total_gross, entry_type='debit'),
                    PayrollPostingLine(account_name=config.paye_liability_account.name, amount=run.total_tax, entry_type='credit'),
                    PayrollPostingLine(account_name=config.pension_liability_account.name, amount=run.total_pension, entry_type='credit'),
                    PayrollPostingLine(account_name=config.net_salary_liability_account.name, amount=run.total_net, entry_type='credit')
                ]

                total_nhf = run.total_gross - run.total_tax - run.total_pension - run.total_net
                if total_nhf > 0:
                    if not config.nhf_liability_account:
                        raise ValidationError("NHF Liability Account must be configured to post payroll runs with NHF deductions.")
                    lines.append(
                        PayrollPostingLine(account_name=config.nhf_liability_account.name, amount=total_nhf, entry_type='credit')
                    )

                command = PayrollPostingCommand(
                    idempotency_key=f"{tenant.id}:{run.id}:v1:post",
                    event_type="salary_payroll_run",
                    tenant_id=str(tenant.id),
                    lines=lines
                )

                # Post to accounting service interface
                accounting_service.post_payroll(command)
                
                run.status = 'posted'
                run.save()

                period = run.period
                period.status = 'closed'
                period.save()

                # Record outbox event on commit
                OutboxService.record_event(
                    tenant=tenant,
                    event_name=DomainEvents.PAYROLL_POSTED,
                    aggregate_type="PayrollRun",
                    aggregate_id=str(run.id),
                    payload={
                        "payroll_run_id": str(run.id),
                        "status": "posted"
                    }
                )
        except Exception as e:
            try:
                run = PayrollRun.objects.get(id=run_id, tenant=tenant)
                run.status = 'posting_failed'
                run.save()
            except Exception:
                pass
            raise e

        return run
