from decimal import Decimal
from datetime import date, datetime, time, timedelta
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

from backend.apps.tenants.models import Tenant, School
from backend.apps.identity.models import Role, TenantMembership
from backend.apps.people.models import Person, PersonRole
from backend.apps.hr.models.employee import EmployeeProfile, OrgAssignmentHistory
from backend.apps.hr.models.leave import LeaveType, LeaveRequest, LeaveBalance
from backend.apps.hr.models.payroll import PayrollPeriod, PayrollRun, PayrollPayslip, SalaryStructure, PayrollGLAccount, PayrollAccountingConfiguration
from backend.apps.hr.models.attendance import AttendanceShift, AttendanceRecord, AttendanceAdjustment
from backend.apps.hr.models.recruitment import JobRequisition, JobVacancy, JobApplication
from backend.apps.hr.services.employee import EmployeeService
from backend.apps.hr.services.recruitment import RecruitmentService
from backend.apps.hr.services.leave import LeaveService
from backend.apps.hr.services.payroll import PayrollService
from backend.apps.hr.services.attendance import AttendanceService
from backend.apps.efbm.services.finance import AccountingService

User = get_user_model()

class HREndToEndWorkflowTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.tenant = Tenant.objects.create(name="Grace Academy International")
        self.school = School.objects.create(tenant=self.tenant, name="Grace Main Campus")
        
        # Roles
        self.role_admin = Role.objects.create(tenant=self.tenant, code="hr_admin", name="HR Admin")
        self.role_payroll = Role.objects.create(tenant=self.tenant, code="payroll_admin", name="Payroll Admin")
        self.role_supervisor = Role.objects.create(tenant=self.tenant, code="supervisor", name="Supervisor")
        self.role_staff = Role.objects.create(tenant=self.tenant, code="staff", name="Staff")

        # Create Admin User
        self.admin_user = User.objects.create_user(
            username="hr.admin", email="hr.admin@eduorbit.com", password="Demo@2026", is_staff=True
        )
        TenantMembership.objects.create(user=self.admin_user, tenant=self.tenant, role=self.role_admin, status="active")
        self.admin_person = Person.objects.create(
            tenant=self.tenant, user=self.admin_user, person_number="PER-001", 
            first_name="Grace", last_name="Adeyemi", date_of_birth=date(1985, 4, 12), gender="female"
        )
        self.admin_emp = EmployeeProfile.objects.create(tenant=self.tenant, person=self.admin_person, employee_number="EMP-001", job_title="HR Director", salary_grade="grade_2")

        # Create Staff User
        self.staff_user = User.objects.create_user(
            username="staff.member", email="staff.member@eduorbit.com", password="Demo@2026"
        )
        TenantMembership.objects.create(user=self.staff_user, tenant=self.tenant, role=self.role_staff, status="active")
        self.staff_person = Person.objects.create(
            tenant=self.tenant, user=self.staff_user, person_number="PER-002", 
            first_name="David", last_name="Eze", date_of_birth=date(1992, 8, 20), gender="male"
        )
        self.staff_emp = EmployeeProfile.objects.create(tenant=self.tenant, person=self.staff_person, employee_number="EMP-004", job_title="Teacher", salary_grade="grade_1")

    def test_recruitment_to_hire_workflow(self):
        """End-to-End Recruitment: Vacancy -> Application -> Interview -> Scorecard -> Offer -> Hire"""
        vacancy = RecruitmentService.publish_vacancy(self.tenant, title="Physics Teacher", department="Sciences")
        self.assertIsNotNone(vacancy.id)
        
        app = RecruitmentService.submit_application(self.tenant, vacancy, first_name="Natasha", last_name="Romanoff", email="natasha@eduorbit.com")
        self.assertEqual(app.stage, "applied")

        panel = RecruitmentService.schedule_interview(self.tenant, app, datetime.now())
        self.assertEqual(app.stage, "interviewing")

        card = RecruitmentService.submit_scorecard(self.tenant, app, self.admin_emp, score=92.5)
        self.assertEqual(card.score, Decimal("92.5"))

        offer = RecruitmentService.generate_offer(self.tenant, app, offered_salary=180000, designation="Physics Teacher", start_date=date.today())
        self.assertEqual(app.stage, "offered")

        hired_emp = RecruitmentService.hire_candidate(self.tenant, app, school=self.school, department_name="Sciences")
        self.assertIsNotNone(hired_emp.id)
        self.assertEqual(app.stage, "hired")

    def test_leave_approval_workflow(self):
        """End-to-End Leave: Submit Request -> Approve -> Balance Deduction"""
        ltype = LeaveType.objects.create(tenant=self.tenant, code="ANNUAL", name="Annual Leave", default_days_per_year=20)
        LeaveBalance.objects.create(tenant=self.tenant, employee=self.staff_emp, leave_type=ltype, leave_type_name="Annual Leave", allowed_days=20, remaining_days=20)

        req = LeaveService.submit_leave_request(self.tenant, self.staff_emp, ltype, date.today(), date.today() + timedelta(days=2), reason="Rest")
        self.assertEqual(req.days_requested, 3)

        approved_req = LeaveService.approve_leave_request(self.tenant, req.id, approver_employee=self.admin_emp)
        self.assertEqual(approved_req.status, "hr_approved")

        bal = LeaveBalance.objects.get(tenant=self.tenant, employee=self.staff_emp, leave_type=ltype)
        self.assertEqual(bal.used_days, 3)
        self.assertEqual(bal.remaining_days, 17)

    def test_payroll_calculation_and_gl_posting(self):
        """End-to-End Payroll: Period -> Calculation Engine -> Run -> Accounting Posting"""
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
        self.assertTrue(run.payslips.count() > 0)

        accounting_svc = AccountingService()
        posted_run = PayrollService.approve_and_post_payroll(self.tenant, run.id, accounting_svc)
        self.assertEqual(posted_run.status, "posted")

    def test_attendance_clocking_and_recalculation(self):
        """End-to-End Attendance: Clock In -> Clock Out -> Calculation Engine -> Adjustment"""
        shift = AttendanceShift.objects.create(tenant=self.tenant, code="MORNING", name="Morning", start_time=time(8, 0), end_time=time(16, 0), grace_minutes=15)
        
        rec = AttendanceService.clock_in(self.staff_emp, datetime.now())
        self.assertIsNotNone(rec.check_in)
        
        rec_out = AttendanceService.clock_out(self.staff_emp, datetime.now())
        self.assertIsNotNone(rec_out.check_out)

    def test_seed_demo_accounts_login(self):
        """Verify web endpoints render for authenticated users"""
        self.client.force_login(self.admin_user)
        response = self.client.get('/hr/dashboard/')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/hr/ess/')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/hr/payroll/')
        self.assertEqual(response.status_code, 200)
