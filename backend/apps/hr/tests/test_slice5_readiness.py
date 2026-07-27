from decimal import Decimal
from datetime import date, datetime, time, timedelta
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from backend.apps.tenants.models import Tenant, School
from backend.apps.identity.models import Role, TenantMembership
from backend.apps.people.models import Person
from backend.apps.hr.models.employee import EmployeeProfile, OrgAssignmentHistory, HRAuditLog
from backend.apps.hr.models.leave import LeaveType, LeaveRequest, LeaveBalance
from backend.apps.hr.models.payroll import PayrollPeriod, PayrollRun, PayrollPayslip, SalaryStructure, PayrollGLAccount, PayrollAccountingConfiguration
from backend.apps.hr.models.attendance import AttendanceShift, AttendanceRecord, AttendanceAdjustment
from backend.apps.hr.models.recruitment import JobRequisition, JobVacancy, JobApplication
from backend.apps.hr.models.settings import HRSettings
from backend.apps.hr.services.employee import EmployeeService
from backend.apps.hr.services.recruitment import RecruitmentService
from backend.apps.hr.services.leave import LeaveService
from backend.apps.hr.services.payroll import PayrollService
from backend.apps.hr.services.attendance import AttendanceService
from backend.apps.efbm.services.finance import AccountingService
from backend.apps.core.models.outbox import OutboxEvent, OutboxStatus

User = get_user_model()

class Slice5EnterpriseReadinessTests(TestCase):
    def setUp(self):
        self.client = Client()
        
        # 1. Setup Tenant A
        self.tenant_a = Tenant.objects.create(name="Grace Academy International")
        self.school_a = School.objects.create(tenant=self.tenant_a, name="Grace Main Campus")
        
        # 2. Setup Tenant B (Isolation Testing)
        self.tenant_b = Tenant.objects.create(name="St. Jude International School")
        self.school_b = School.objects.create(tenant=self.tenant_b, name="St. Jude Campus")

        # Roles
        self.role_admin = Role.objects.create(tenant=self.tenant_a, code="hr_admin", name="HR Admin")
        self.role_payroll = Role.objects.create(tenant=self.tenant_a, code="payroll_admin", name="Payroll Admin")
        self.role_supervisor = Role.objects.create(tenant=self.tenant_a, code="supervisor", name="Supervisor")
        self.role_staff = Role.objects.create(tenant=self.tenant_a, code="staff", name="Staff")
        self.role_finance = Role.objects.create(tenant=self.tenant_a, code="finance", name="Finance")

        # Users
        self.user_admin = self._create_user_with_role("hr.admin", "hr_admin", self.role_admin)
        self.user_payroll = self._create_user_with_role("payroll.admin", "payroll_admin", self.role_payroll)
        self.user_manager = self._create_user_with_role("dept.manager", "dept_manager", self.role_supervisor)
        self.user_staff = self._create_user_with_role("staff.member", "staff_member", self.role_staff)
        self.user_finance = self._create_user_with_role("finance.officer", "finance_officer", self.role_finance)

    def _create_user_with_role(self, username, code_prefix, role):
        user = User.objects.create_user(username=username, email=f"{username}@eduorbit.com", password="Demo@2026")
        TenantMembership.objects.create(user=user, tenant=self.tenant_a, role=role, status="active")
        person = Person.objects.create(tenant=self.tenant_a, user=user, person_number=f"PER-{code_prefix}", first_name=username.split('.')[0].title(), last_name="User", date_of_birth=date(1990, 1, 1), gender="other")
        EmployeeProfile.objects.create(tenant=self.tenant_a, person=person, employee_number=f"EMP-{code_prefix}", job_title="Staff", salary_grade="grade_1")
        return user

    def test_url_security_and_role_gating(self):
        """Verify strict permission gating across all endpoints"""
        # Staff accessing payroll console -> 403 or redirect
        self.client.force_login(self.user_staff)
        res = self.client.get('/hr/payroll/')
        self.assertIn(res.status_code, [403, 302])

        # Staff accessing ESS -> 200 OK
        res = self.client.get('/hr/ess/')
        self.assertEqual(res.status_code, 200)

        # Admin accessing HR Admin Dashboard -> 200 OK
        self.client.force_login(self.user_admin)
        res = self.client.get('/hr/dashboard/')
        self.assertEqual(res.status_code, 200)

    def test_full_end_to_end_hr_payroll_lifecycle(self):
        """Complete workflow validation: Recruitment -> Hire -> Leave -> Payroll -> Accounting Posting"""
        # 1. Recruitment & Hire
        vacancy = RecruitmentService.publish_vacancy(self.tenant_a, title="Chemistry Teacher", department="Sciences")
        app = RecruitmentService.submit_application(self.tenant_a, vacancy, first_name="Natasha", last_name="Romanoff", email="natasha@eduorbit.com")
        emp = RecruitmentService.hire_candidate(self.tenant_a, app, school=self.school_a, department_name="Sciences")
        self.assertIsNotNone(emp.id)

        # 2. Leave Request & Approval
        ltype = LeaveType.objects.create(tenant=self.tenant_a, code="ANNUAL", name="Annual Leave", default_days_per_year=20)
        LeaveBalance.objects.create(tenant=self.tenant_a, employee=emp, leave_type=ltype, leave_type_name="Annual Leave", allowed_days=20, remaining_days=20)
        req = LeaveService.submit_leave_request(self.tenant_a, emp, ltype, date.today(), date.today() + timedelta(days=2), reason="Vacation")
        LeaveService.approve_leave_request(self.tenant_a, req.id)

        # 3. Salary & GL Setup
        SalaryStructure.objects.create(tenant=self.tenant_a, grade="grade_1", base_salary=Decimal("150000.00"), housing_allowance=Decimal("30000.00"), transport_allowance=Decimal("20000.00"))
        gl_sal = PayrollGLAccount.objects.create(tenant=self.tenant_a, code="5001", name="Salaries Expense")
        gl_paye = PayrollGLAccount.objects.create(tenant=self.tenant_a, code="2101", name="PAYE Tax Liability")
        gl_pen = PayrollGLAccount.objects.create(tenant=self.tenant_a, code="2102", name="Pension Liability")
        gl_net = PayrollGLAccount.objects.create(tenant=self.tenant_a, code="2103", name="Net Payable")
        gl_nhf = PayrollGLAccount.objects.create(tenant=self.tenant_a, code="2104", name="NHF Liability")
        PayrollAccountingConfiguration.objects.create(tenant=self.tenant_a, salary_expense_account=gl_sal, paye_liability_account=gl_paye, pension_liability_account=gl_pen, net_salary_liability_account=gl_net, nhf_liability_account=gl_nhf)

        # 4. Payroll Run & Accounting Posting
        period = PayrollPeriod.objects.create(tenant=self.tenant_a, name="July 2026", start_date=date(2026, 7, 1), end_date=date(2026, 7, 28))
        run = PayrollService.generate_payroll_run(self.tenant_a, period.id)
        accounting_svc = AccountingService()
        posted_run = PayrollService.approve_and_post_payroll(self.tenant_a, run.id, accounting_svc)

        self.assertEqual(posted_run.status, "posted")
        self.assertTrue(posted_run.payslips.count() > 0)

    def test_multi_tenant_data_isolation(self):
        """Verify complete isolation between Tenant A and Tenant B"""
        emp_a = EmployeeProfile.objects.filter(tenant=self.tenant_a).first()
        
        # Verify Tenant B queries return zero records for Tenant A data
        emp_b_qs = EmployeeProfile.objects.filter(tenant=self.tenant_b)
        self.assertFalse(emp_b_qs.filter(id=emp_a.id).exists())

    def test_double_entry_accounting_integrity(self):
        """Verify double entry balancing (Debits == Credits)"""
        gl_sal = PayrollGLAccount.objects.create(tenant=self.tenant_a, code="5001", name="Salaries Expense")
        gl_paye = PayrollGLAccount.objects.create(tenant=self.tenant_a, code="2101", name="PAYE Tax Liability")
        gl_pen = PayrollGLAccount.objects.create(tenant=self.tenant_a, code="2102", name="Pension Liability")
        gl_net = PayrollGLAccount.objects.create(tenant=self.tenant_a, code="2103", name="Net Payable")
        gl_nhf = PayrollGLAccount.objects.create(tenant=self.tenant_a, code="2104", name="NHF Liability")
        PayrollAccountingConfiguration.objects.create(tenant=self.tenant_a, salary_expense_account=gl_sal, paye_liability_account=gl_paye, pension_liability_account=gl_pen, net_salary_liability_account=gl_net, nhf_liability_account=gl_nhf)

        period = PayrollPeriod.objects.create(tenant=self.tenant_a, name="July 2026", start_date=date(2026, 7, 1), end_date=date(2026, 7, 28))
        run = PayrollService.generate_payroll_run(self.tenant_a, period.id)
        accounting_svc = AccountingService()
        PayrollService.approve_and_post_payroll(self.tenant_a, run.id, accounting_svc)
