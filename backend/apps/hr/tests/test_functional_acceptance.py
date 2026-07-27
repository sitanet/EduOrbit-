from decimal import Decimal
from datetime import date, datetime, time, timedelta
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

from backend.apps.tenants.models import Tenant, School
from backend.apps.identity.models import Role, TenantMembership
from backend.apps.people.models import Person
from backend.apps.hr.models.employee import EmployeeProfile, OrgAssignmentHistory, HRAuditLog
from backend.apps.hr.models.leave import LeaveType, LeaveRequest, LeaveBalance, PublicHoliday
from backend.apps.hr.models.payroll import PayrollPeriod, PayrollRun, PayrollPayslip, SalaryStructure, PayrollGLAccount, PayrollAccountingConfiguration
from backend.apps.hr.models.attendance import AttendanceShift, AttendanceRecord, AttendanceAdjustment, EmployeeShiftAssignment
from backend.apps.hr.models.recruitment import JobRequisition, JobVacancy, JobApplication, InterviewScorecard, OfferLetter
from backend.apps.hr.models.settings import HRSettings
from backend.apps.hr.services.employee import EmployeeService
from backend.apps.hr.services.recruitment import RecruitmentService
from backend.apps.hr.services.leave import LeaveService
from backend.apps.hr.services.payroll import PayrollService
from backend.apps.hr.services.attendance import AttendanceService
from backend.apps.efbm.services.finance import AccountingService

User = get_user_model()

class HRFunctionalAcceptanceAuditTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.tenant = Tenant.objects.create(name="Grace Academy International")
        self.school = School.objects.create(tenant=self.tenant, name="Grace Main Campus")

        # Setup 6 Roles
        self.role_admin = Role.objects.create(tenant=self.tenant, code="hr_admin", name="HR Admin")
        self.role_officer = Role.objects.create(tenant=self.tenant, code="hr_officer", name="HR Officer")
        self.role_payroll = Role.objects.create(tenant=self.tenant, code="payroll_admin", name="Payroll Admin")
        self.role_supervisor = Role.objects.create(tenant=self.tenant, code="supervisor", name="Supervisor")
        self.role_staff = Role.objects.create(tenant=self.tenant, code="staff", name="Staff")
        self.role_finance = Role.objects.create(tenant=self.tenant, code="finance", name="Finance")

        # Setup Users
        self.user_admin = self._create_user("hr.admin", self.role_admin)
        self.user_officer = self._create_user("hr.officer", self.role_officer)
        self.user_payroll = self._create_user("payroll.admin", self.role_payroll)
        self.user_supervisor = self._create_user("dept.manager", self.role_supervisor)
        self.user_staff = self._create_user("staff.member", self.role_staff)
        self.user_finance = self._create_user("finance.officer", self.role_finance)

    def _create_user(self, username, role):
        user = User.objects.create_user(username=username, email=f"{username}@eduorbit.com", password="Demo@2026")
        TenantMembership.objects.create(user=user, tenant=self.tenant, role=role, status="active")
        person = Person.objects.create(tenant=self.tenant, user=user, person_number=f"PER-{username}", first_name=username.split('.')[0].title(), last_name="User", date_of_birth=date(1990, 1, 1), gender="other")
        EmployeeProfile.objects.create(tenant=self.tenant, person=person, employee_number=f"EMP-{username}", job_title="Staff", salary_grade="grade_1")
        return user

    def test_all_18_web_urls_load_without_500_or_404(self):
        """Phase 1 Audit: Verify all 18 web view URLs return 200 for authorized HR Admin"""
        self.client.force_login(self.user_admin)
        urls_to_test = [
            '/hr/dashboard/',
            '/hr/ess/',
            '/hr/manager/team/',
            '/hr/admin/directory/',
            '/hr/admin/org-chart/',
            '/hr/recruitment/',
            '/hr/leave-calendar/',
            '/hr/attendance/',
            '/hr/payroll/',
            '/hr/finance/postings/',
            '/hr/performance/',
            '/hr/training/',
            '/hr/disciplinary/',
            '/hr/rewards/',
            '/hr/analytics/',
            '/hr/notifications/',
            '/hr/audit/',
            '/hr/settings/',
            '/hr/import/',
            '/hr/bulk/',
            '/hr/search/',
            '/hr/reports/',
        ]
        for url in urls_to_test:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, f"URL {url} failed with status {response.status_code}")

    def test_payroll_audit_full_cycle(self):
        """Phase 5 Audit: Payroll generation, approval, double-entry GL posting, and payslips"""
        emp = EmployeeProfile.objects.filter(tenant=self.tenant, person__user=self.user_staff).first()
        SalaryStructure.objects.create(tenant=self.tenant, grade="grade_1", base_salary=Decimal("150000.00"), housing_allowance=Decimal("30000.00"), transport_allowance=Decimal("20000.00"))

        gl_sal = PayrollGLAccount.objects.create(tenant=self.tenant, code="5001", name="Salary Expense")
        gl_paye = PayrollGLAccount.objects.create(tenant=self.tenant, code="2101", name="PAYE Tax Liability")
        gl_pen = PayrollGLAccount.objects.create(tenant=self.tenant, code="2102", name="Pension Liability")
        gl_net = PayrollGLAccount.objects.create(tenant=self.tenant, code="2103", name="Net Payable")
        gl_nhf = PayrollGLAccount.objects.create(tenant=self.tenant, code="2104", name="NHF Liability")

        PayrollAccountingConfiguration.objects.create(
            tenant=self.tenant, salary_expense_account=gl_sal, paye_liability_account=gl_paye,
            pension_liability_account=gl_pen, net_salary_liability_account=gl_net, nhf_liability_account=gl_nhf
        )

        period = PayrollPeriod.objects.create(tenant=self.tenant, name="July 2026", start_date=date(2026, 7, 1), end_date=date(2026, 7, 28))
        run = PayrollService.generate_payroll_run(self.tenant, period.id)
        self.assertEqual(run.status, "calculated")

        accounting_svc = AccountingService()
        posted_run = PayrollService.approve_and_post_payroll(self.tenant, run.id, accounting_svc)
        self.assertEqual(posted_run.status, "posted")
        self.assertTrue(PayrollPayslip.objects.filter(tenant=self.tenant, payroll_run=posted_run).exists())

    def test_leave_audit_full_cycle(self):
        """Phase 7 Audit: Leave request, approval chain, balance deduction"""
        emp = EmployeeProfile.objects.filter(tenant=self.tenant, person__user=self.user_staff).first()
        ltype = LeaveType.objects.create(tenant=self.tenant, code="ANNUAL", name="Annual Leave", default_days_per_year=20)
        LeaveBalance.objects.create(tenant=self.tenant, employee=emp, leave_type=ltype, leave_type_name="Annual Leave", allowed_days=20, remaining_days=20)

        req = LeaveService.submit_leave_request(self.tenant, emp, ltype, date.today(), date.today() + timedelta(days=1), reason="Vacation")
        self.assertEqual(req.status, "submitted")

        admin_emp = EmployeeProfile.objects.filter(tenant=self.tenant, person__user=self.user_admin).first()
        approved = LeaveService.approve_leave_request(self.tenant, req.id, approver_employee=admin_emp)
        self.assertEqual(approved.status, "hr_approved")

        bal = LeaveBalance.objects.get(tenant=self.tenant, employee=emp, leave_type=ltype)
        self.assertEqual(bal.remaining_days, 18)

    def test_recruitment_audit_full_cycle(self):
        """Phase 8 Audit: Vacancy -> Application -> Scorecard -> Offer -> Hire"""
        admin_emp = EmployeeProfile.objects.filter(tenant=self.tenant, person__user=self.user_admin).first()
        vacancy = RecruitmentService.publish_vacancy(self.tenant, title="Mathematics Teacher", department="Academics")
        app = RecruitmentService.submit_application(self.tenant, vacancy, first_name="Bruce", last_name="Banner", email="bruce@eduorbit.com")
        card = RecruitmentService.submit_scorecard(self.tenant, app, admin_emp, score=95.0)
        offer = RecruitmentService.generate_offer(self.tenant, app, offered_salary=200000, designation="Mathematics Teacher", start_date=date.today())
        emp = RecruitmentService.hire_candidate(self.tenant, app, school=self.school)
        self.assertEqual(app.stage, "hired")
        self.assertIsNotNone(emp.id)

    def test_attendance_audit_clocking(self):
        """Phase 6 Audit: Clock in & clock out event handling"""
        emp = EmployeeProfile.objects.filter(tenant=self.tenant, person__user=self.user_staff).first()
        shift = AttendanceShift.objects.create(tenant=self.tenant, code="MORNING", name="Morning Shift", start_time=time(8, 0), end_time=time(16, 0), grace_minutes=15)
        EmployeeShiftAssignment.objects.create(tenant=self.tenant, employee=emp, shift=shift, effective_from=date(2026, 1, 1))

        from django.utils import timezone
        now = timezone.now() - timedelta(hours=9)
        rec_in = AttendanceService.clock_in(emp, now)
        self.assertIsNotNone(rec_in.check_in)

        rec_out = AttendanceService.clock_out(emp, now + timedelta(hours=8))
        self.assertIsNotNone(rec_out.check_out)

    def test_reports_export_formats(self):
        """Phase 10 Audit: Verify CSV and PDF export endpoints return 200 OK"""
        self.client.force_login(self.user_admin)
        res_csv = self.client.get('/hr/attendance/report/?format=csv')
        self.assertEqual(res_csv.status_code, 200)
        self.assertEqual(res_csv['Content-Type'], 'text/csv')

        res_pdf = self.client.get('/hr/attendance/report/?format=pdf')
        self.assertEqual(res_pdf.status_code, 200)
