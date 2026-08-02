from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from datetime import date, timedelta, time, datetime
from django.db import transaction
from unittest.mock import patch, MagicMock
from backend.apps.core.events import event_bus, DomainEvent
from backend.apps.tenants.models import Tenant, School
from backend.apps.people.models import Person
from backend.apps.hr.models import (
    EmployeeProfile, JobRequisition, JobVacancy, JobApplication, InterviewPanel, InterviewScorecard, OfferLetter, OnboardingTask, HRSettings, LeaveType, LeavePolicy, LeaveRequest, LeaveBalance, PublicHoliday, LeaveEncashment
)
from backend.apps.hr.services import EmployeeService, RecruitmentService, OnboardingService, LeaveService
from backend.apps.hr.selectors import EmployeeSelector, RecruitmentSelector, OnboardingSelector, HRSettingsSelector, LeaveSelector
from backend.apps.hr.validators import EmployeeValidator, RecruitmentValidator, LeaveValidator

class Slice1EmployeeRecruitmentOnboardingTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Slice 1 Org")
        self.school = School.objects.create(tenant=self.tenant, name="Slice 1 High School", school_types=["secondary"])

    def test_employee_service_creation(self):
        emp = EmployeeService.create_employee(
            tenant=self.tenant,
            first_name="Tony",
            last_name="Stark",
            email="tony@eduorbit.com",
            job_title="Physics Teacher",
            salary_grade="grade_3",
            school=self.school
        )
        self.assertIsNotNone(emp.id)
        self.assertEqual(emp.person.first_name, "Tony")
        self.assertEqual(emp.person.user.email, "tony@eduorbit.com")
        self.assertEqual(emp.status, "active")
        self.assertEqual(emp.confirmation_status, "probation")

    def test_employee_status_transition(self):
        emp = EmployeeService.create_employee(
            tenant=self.tenant,
            first_name="Steve",
            last_name="Rogers",
            email="steve@eduorbit.com",
            job_title="PE Instructor"
        )
        updated = EmployeeService.transition_status(self.tenant, emp.id, "confirmed")
        self.assertEqual(updated.status, "confirmed")
        self.assertEqual(updated.confirmation_status, "confirmed")

    def test_recruitment_pipeline_workflow(self):
        emp = EmployeeService.create_employee(
            tenant=self.tenant,
            first_name="Bruce",
            last_name="Banner",
            email="bruce@eduorbit.com",
            job_title="HR Manager"
        )
        
        req = RecruitmentService.create_requisition(self.tenant, emp, "Chemistry Teacher", "Sciences", 2)
        vac = RecruitmentService.publish_vacancy(self.tenant, "Chemistry Teacher", "Sciences", requisition=req)
        app = RecruitmentService.submit_application(self.tenant, vac, "Peter", "Parker", "peter@eduorbit.com")
        panel = RecruitmentService.schedule_interview(self.tenant, app, timezone.now())
        card = RecruitmentService.submit_scorecard(self.tenant, app, emp, 95.00, "Excellent candidate")
        offer = RecruitmentService.generate_offer(self.tenant, app, 85000.00, "Chemistry Teacher", timezone.now().date())
        new_emp = RecruitmentService.hire_candidate(self.tenant, app, school=self.school)
        self.assertEqual(app.stage, "hired")

    def test_onboarding_task_seeding_and_toggle(self):
        emp = EmployeeService.create_employee(
            tenant=self.tenant,
            first_name="Wanda",
            last_name="Maximoff",
            email="wanda@eduorbit.com",
            job_title="Counselor"
        )
        tasks = OnboardingService.seed_default_tasks(self.tenant, emp)
        self.assertEqual(len(tasks), 5)
        t0_updated = OnboardingService.toggle_task(self.tenant, tasks[0].id, is_completed=True)
        self.assertTrue(t0_updated.is_completed)


class Slice2LeaveManagementTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Slice 2 Org")
        self.school = School.objects.create(tenant=self.tenant, name="Slice 2 High School", school_types=["secondary"])
        self.employee = EmployeeService.create_employee(
            tenant=self.tenant,
            first_name="Clint",
            last_name="Barton",
            email="clint@eduorbit.com",
            job_title="Archery Instructor"
        )
        self.leave_type = LeaveType.objects.create(
            tenant=self.tenant,
            name="Annual Leave",
            code="AL",
            default_days_per_year=20,
            allow_encashment=True
        )

    def test_leave_request_submission_and_approval_workflow(self):
        start_d = timezone.now().date() + timedelta(days=5)
        end_d = start_d + timedelta(days=4)  # 5 days
        
        req = LeaveService.submit_leave_request(
            tenant=self.tenant,
            employee=self.employee,
            leave_type=self.leave_type,
            start_date=start_d,
            end_date=end_d,
            reason="Family vacation"
        )
        self.assertEqual(req.days_requested, 5)
        self.assertEqual(req.status, "submitted")
        
        approved_req = LeaveService.approve_leave_request(self.tenant, req.id)
        self.assertEqual(approved_req.status, "hr_approved")
        
        bal = LeaveBalance.objects.get(tenant=self.tenant, employee=self.employee, leave_type=self.leave_type)
        self.assertEqual(bal.used_days, 5)
        self.assertEqual(bal.remaining_days, 15)

    def test_leave_rejection(self):
        start_d = timezone.now().date() + timedelta(days=10)
        end_d = start_d + timedelta(days=1)
        
        req = LeaveService.submit_leave_request(
            tenant=self.tenant,
            employee=self.employee,
            leave_type=self.leave_type,
            start_date=start_d,
            end_date=end_d
        )
        rejected = LeaveService.reject_leave_request(self.tenant, req.id, reason="Peak exam period")
        self.assertEqual(rejected.status, "rejected")

    def test_leave_encashment(self):
        bal = LeaveBalance.objects.create(
            tenant=self.tenant,
            employee=self.employee,
            leave_type=self.leave_type,
            allowed_days=20,
            remaining_days=15
        )
        encashment = LeaveService.encash_leave(self.tenant, self.employee, self.leave_type, days_to_encash=5, daily_rate=2000.00)
        self.assertEqual(encashment.amount, 10000.00)
        self.assertEqual(encashment.status, "submitted")

    def test_leave_selectors(self):
        types = LeaveSelector.get_leave_types(self.tenant)
        self.assertEqual(types.count(), 1)
        
        holidays = LeaveSelector.get_public_holidays(self.tenant)
        self.assertEqual(holidays.count(), 0)


class EventInfrastructureTests(TransactionTestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Event Infra Org")
        self.school = School.objects.create(tenant=self.tenant, name="Infra School", school_types=["secondary"])
        self.employee = EmployeeService.create_employee(
            tenant=self.tenant,
            first_name="Peter",
            last_name="Parker",
            email="peter@eduorbit.com",
            job_title="Science Teacher",
            school=self.school
        )
        self.leave_type = LeaveType.objects.create(
            tenant=self.tenant,
            name="Annual Leave",
            code="ANNUAL",
            default_days_per_year=20
        )

    @patch('backend.apps.core.events.DomainEventBus.publish')
    def test_employee_created_publishes_after_commit(self, mock_publish):
        with transaction.atomic():
            emp = EmployeeService.create_employee(
                tenant=self.tenant,
                first_name="Bruce",
                last_name="Banner",
                email="bruce@eduorbit.com",
                job_title="Bio Teacher",
                school=self.school
            )
            # Before commit, no events should be published
            mock_publish.assert_not_called()
            
        # After transaction commits, event should be published
        self.assertTrue(mock_publish.called)
        # Check event name
        args, _ = mock_publish.call_args
        self.assertEqual(args[0].event_name, "employee.created")

    @patch('backend.apps.core.events.DomainEventBus.publish')
    def test_leave_requested_publishes_after_commit(self, mock_publish):
        start_d = timezone.now().date() + timedelta(days=5)
        end_d = start_d + timedelta(days=2)
        with transaction.atomic():
            LeaveService.submit_leave_request(
                tenant=self.tenant,
                employee=self.employee,
                leave_type=self.leave_type,
                start_date=start_d,
                end_date=end_d
            )
            mock_publish.assert_not_called()
            
        self.assertTrue(mock_publish.called)
        args, _ = mock_publish.call_args
        self.assertEqual(args[0].event_name, "leave.requested")

    @patch('backend.apps.core.events.DomainEventBus.publish')
    def test_leave_approved_publishes_after_commit(self, mock_publish):
        start_d = timezone.now().date() + timedelta(days=5)
        end_d = start_d + timedelta(days=2)
        req = LeaveService.submit_leave_request(
            tenant=self.tenant,
            employee=self.employee,
            leave_type=self.leave_type,
            start_date=start_d,
            end_date=end_d
        )
        mock_publish.reset_mock()
        
        with transaction.atomic():
            LeaveService.approve_leave_request(self.tenant, req.id)
            mock_publish.assert_not_called()
            
        self.assertTrue(mock_publish.called)
        args, _ = mock_publish.call_args
        self.assertEqual(args[0].event_name, "leave.approved")

    @patch('backend.apps.core.tasks.dispatch_async_event.delay')
    def test_redis_unavailable_does_not_rollback(self, mock_delay):
        # Redis connection failure raises an exception (actively refused)
        mock_delay.side_effect = ConnectionError("Redis connection refused")
        
        start_d = timezone.now().date() + timedelta(days=5)
        end_d = start_d + timedelta(days=2)
        
        # This should execute and commit successfully despite Redis failure
        req = LeaveService.submit_leave_request(
            tenant=self.tenant,
            employee=self.employee,
            leave_type=self.leave_type,
            start_date=start_d,
            end_date=end_d
        )
        self.assertIsNotNone(req)
        # Verify LeaveRequest exists in database
        self.assertTrue(LeaveRequest.objects.filter(id=req.id).exists())

    def test_on_commit_callback_executes_exactly_once(self):
        call_count = 0
        def callback():
            nonlocal call_count
            call_count += 1
            
        with transaction.atomic():
            transaction.on_commit(callback)
            self.assertEqual(call_count, 0)
            
        self.assertEqual(call_count, 1)

    def test_multiple_callbacks_order(self):
        execution_order = []
        with transaction.atomic():
            transaction.on_commit(lambda: execution_order.append(1))
            transaction.on_commit(lambda: execution_order.append(2))
            transaction.on_commit(lambda: execution_order.append(3))
            self.assertEqual(execution_order, [])
            
        self.assertEqual(execution_order, [1, 2, 3])


from decimal import Decimal
from django.core.exceptions import ValidationError
from backend.apps.hr.models.payroll import (
    PayrollPeriod, SalaryStructure, PayrollRun, PayrollPayslip, 
    PayrollAccountingConfiguration, PayrollGLAccount
)
from backend.apps.hr.services.payroll import PayrollCalculationEngineV1, PayrollService
from backend.apps.efbm.services.finance import AccountingService
from backend.apps.core.models.outbox import OutboxEvent, OutboxStatus
from backend.apps.core.services.outbox import OutboxService
from backend.apps.core.interfaces import AccountingPostingInterface
from backend.apps.core.models.processed_event import ProcessedEvent
from backend.apps.core.tasks import process_pending_outbox, recover_orphaned_locks, archive_processed_outbox

class PayrollIntegrationTests(TransactionTestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Payroll Tenant")
        self.school = School.objects.create(tenant=self.tenant, name="Payroll School", school_types=["secondary"])
        
        # Create GL Accounts
        self.salary_exp = PayrollGLAccount.objects.create(tenant=self.tenant, code="SAL_EXP", name="Salary Expense")
        self.paye_liab = PayrollGLAccount.objects.create(tenant=self.tenant, code="PAYE_LIAB", name="PAYE Liability")
        self.pension_liab = PayrollGLAccount.objects.create(tenant=self.tenant, code="PEN_LIAB", name="Pension Liability")
        self.net_liab = PayrollGLAccount.objects.create(tenant=self.tenant, code="NET_LIAB", name="Bank Net Salary Liability")
        self.nhf_liab = PayrollGLAccount.objects.create(tenant=self.tenant, code="NHF_LIAB", name="NHF Liability")
        
        # Create configuration
        self.config = PayrollAccountingConfiguration.objects.create(
            tenant=self.tenant,
            salary_expense_account=self.salary_exp,
            paye_liability_account=self.paye_liab,
            pension_liability_account=self.pension_liab,
            net_salary_liability_account=self.net_liab,
            nhf_liability_account=self.nhf_liab
        )

        # Create period
        self.period = PayrollPeriod.objects.create(
            tenant=self.tenant,
            name="January 2026",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31)
        )
        
        # Create employees
        self.emp1 = EmployeeService.create_employee(
            tenant=self.tenant,
            first_name="Carol",
            last_name="Danvers",
            email="carol@eduorbit.com",
            job_title="Math Teacher",
            salary_grade="grade_A",
            school=self.school
        )
        self.emp2 = EmployeeService.create_employee(
            tenant=self.tenant,
            first_name="Wanda",
            last_name="Maximoff",
            email="wanda@eduorbit.com",
            job_title="Art Teacher",
            salary_grade="grade_B",
            school=self.school
        )
        
        # Create structures
        self.structure1 = SalaryStructure.objects.create(
            tenant=self.tenant,
            grade="grade_A",
            base_salary=200000.00,
            housing_allowance=30000.00,
            transport_allowance=20000.00
        )
        self.structure2 = SalaryStructure.objects.create(
            tenant=self.tenant,
            grade="grade_B",
            base_salary=150000.00,
            housing_allowance=20000.00,
            transport_allowance=10000.00
        )

    def test_stateless_calculation_engine_accuracy(self):
        res = PayrollCalculationEngineV1.calculate(
            base_salary=200000.00,
            housing_allowance=30000.00,
            transport_allowance=20000.00,
            pension_rate=8.00,
            tax_formula='statutory_graduated'
        )
        self.assertEqual(res.gross_pay, Decimal('250000.00'))
        self.assertEqual(res.pension_amount, Decimal('16000.00')) # 8% of 200000 basic
        self.assertEqual(res.nhf_amount, Decimal('5000.00')) # 2.5% of 200000 basic
        
        # Taxable income = 250000 - 16000 - 5000 = 229000
        # 50k @ 5% = 2500
        # 100k @ 10% = 10000
        # Remaining 79k @ 15% = 11850
        # Total tax = 24350.00
        self.assertEqual(res.tax_amount, Decimal('24350.00'))
        self.assertEqual(res.net_pay, Decimal('250000.00') - Decimal('16000.00') - Decimal('5000.00') - Decimal('24350.00'))

    def test_gl_balance_double_entry_constraint(self):
        run = PayrollService.generate_payroll_run(self.tenant, self.period.id)
        accounting_service = AccountingService()
        
        # Clear outbox so we can test posting isolation
        OutboxEvent.objects.all().delete()
        
        posted_run = PayrollService.approve_and_post_payroll(self.tenant, run.id, accounting_service)
        self.assertEqual(posted_run.status, 'posted')
        
        # Verify double entry postings: sum debits == sum credits
        from backend.apps.efbm.models import JournalEntry
        entries = JournalEntry.objects.filter(tenant=self.tenant)
        self.assertTrue(entries.exists())
        
        debits = sum(e.amount for e in entries if e.entry_type == 'debit')
        credits = sum(e.amount for e in entries if e.entry_type == 'credit')
        self.assertEqual(debits, credits)
        self.assertEqual(debits, run.total_gross)

    @patch('backend.apps.core.tasks.dispatch_async_event.delay')
    def test_outbox_creation_and_batch_dispatch(self, mock_delay):
        OutboxEvent.objects.all().delete()
        
        # Generate run should record a payroll.generated outbox event
        run = PayrollService.generate_payroll_run(self.tenant, self.period.id)
        
        # Check outbox event exists
        events = OutboxEvent.objects.filter(tenant=self.tenant, status=OutboxStatus.PENDING)
        self.assertEqual(events.count(), 1)
        event = events.first()
        self.assertEqual(event.event_name, "payroll.generated")
        self.assertEqual(event.sequence_number, 1)

        # Run outbox processor task
        processed = process_pending_outbox()
        self.assertEqual(processed, 1)
        
        # Assert event state updated
        event.refresh_from_db()
        self.assertEqual(event.status, OutboxStatus.PROCESSED)
        self.assertTrue(mock_delay.called)

    def test_concurrency_and_idempotency(self):
        run = PayrollService.generate_payroll_run(self.tenant, self.period.id)
        accounting_service = AccountingService()
        
        # Approve first time
        PayrollService.approve_and_post_payroll(self.tenant, run.id, accounting_service)
        
        # Approve second time should not duplicate journal entries or crash
        # (It should raise ValidationError because run status is already posted, or return cleanly depending on service layer checks)
        with self.assertRaises(ValidationError):
            PayrollService.approve_and_post_payroll(self.tenant, run.id, accounting_service)

    def test_rollback_integrity(self):
        run = PayrollService.generate_payroll_run(self.tenant, self.period.id)
        
        # Mock accounting service that throws a failure
        class FailingAccountingService(AccountingPostingInterface):
            def post_payroll(self, command):
                raise RuntimeError("GL Connection Lost")
                
        failing_service = FailingAccountingService()
        
        with self.assertRaises(RuntimeError):
            PayrollService.approve_and_post_payroll(self.tenant, run.id, failing_service)
            
        # Verify run status rolled back/updated to posting_failed
        run.refresh_from_db()
        self.assertEqual(run.status, 'posting_failed')

    @patch('backend.apps.core.tasks.dispatch_async_event.delay')
    def test_outbox_retry_and_dead_letter(self, mock_delay):
        OutboxEvent.objects.all().delete()
        mock_delay.side_effect = ConnectionError("Broker Down")
        
        # Create an outbox event
        OutboxService.record_event(
            tenant=self.tenant,
            event_name="test.event",
            aggregate_type="TestAgg",
            aggregate_id="123",
            payload={"foo": "bar"}
        )
        
        # First process attempt should fail
        processed = process_pending_outbox()
        self.assertEqual(processed, 0)
        
        event = OutboxEvent.objects.first()
        self.assertEqual(event.status, OutboxStatus.FAILED)
        self.assertEqual(event.dispatch_attempts, 1)
        self.assertIsNotNone(event.next_retry_at)

    def test_multitenant_isolation(self):
        # Create tenant B
        tenant_b = Tenant.objects.create(name="Tenant B")
        gl_exp_b = PayrollGLAccount.objects.create(tenant=tenant_b, code="SAL_EXP_B", name="Salary Expense")
        gl_paye_b = PayrollGLAccount.objects.create(tenant=tenant_b, code="PAYE_B", name="PAYE Liability")
        gl_pen_b = PayrollGLAccount.objects.create(tenant=tenant_b, code="PEN_B", name="Pension Liability")
        gl_net_b = PayrollGLAccount.objects.create(tenant=tenant_b, code="NET_B", name="Bank Net Salary Liability")
        gl_nhf_b = PayrollGLAccount.objects.create(tenant=tenant_b, code="NHF_B", name="NHF Liability")
        
        PayrollAccountingConfiguration.objects.create(
            tenant=tenant_b,
            salary_expense_account=gl_exp_b,
            paye_liability_account=gl_paye_b,
            pension_liability_account=gl_pen_b,
            net_salary_liability_account=gl_net_b,
            nhf_liability_account=gl_nhf_b
        )
        
        period_b = PayrollPeriod.objects.create(
            tenant=tenant_b,
            name="Jan B",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31)
        )
        
        # Verify Tenant A generation does not process Tenant B period
        run_a = PayrollService.generate_payroll_run(self.tenant, self.period.id)
        
        # Verify isolation
        self.assertEqual(PayrollRun.objects.filter(tenant=tenant_b).count(), 0)
        self.assertEqual(PayrollRun.objects.filter(tenant=self.tenant).count(), 1)


class AttendanceIntegrationTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Attendance Tenant")
        
        # Create user & employee profile
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.user = User.objects.create_user(username="att_emp", email="att_emp@test.com", password="password123")
        from backend.apps.people.models import Person
        self.person = Person.objects.create(
            tenant=self.tenant,
            user=self.user,
            person_number="PER-ATT-001",
            first_name="Attendance",
            last_name="Employee",
            date_of_birth=date(1990, 1, 1),
            gender="male"
        )
        self.employee = EmployeeProfile.objects.create(
            tenant=self.tenant,
            person=self.person,
            employee_number="EMP-ATT-001",
            salary_grade="Grade_A",
            joined_date=date(2026, 1, 1)
        )
        
        # Define Shift
        from backend.apps.hr.models.attendance import AttendanceShift, EmployeeShiftAssignment
        self.shift = AttendanceShift.objects.create(
            tenant=self.tenant,
            name="Day Shift",
            code="DAY",
            start_time=time(9, 0),
            end_time=time(17, 0),
            grace_minutes=15,
            break_start=time(12, 0),
            break_end=time(13, 0),
            minimum_hours=Decimal('4.00'),
            overtime_after=Decimal('8.00'),
            overnight_shift=False
        )
        
        # Assign shift
        EmployeeShiftAssignment.objects.create(
            tenant=self.tenant,
            employee=self.employee,
            shift=self.shift,
            effective_from=date(2026, 1, 1)
        )

    def test_shift_calculations_accuracy(self):
        from backend.apps.hr.services.calculations import AttendanceCalculationEngineV1
        
        # 1. Normal Check-in Check-out
        in_dt = datetime(2026, 1, 1, 9, 0)
        out_dt = datetime(2026, 1, 1, 17, 0)
        
        res = AttendanceCalculationEngineV1.calculate(
            check_in_dt=in_dt,
            check_out_dt=out_dt,
            shift=self.shift
        )
        # Total working hours = 8 hrs minus 1 hr break = 7 hrs
        self.assertEqual(res.total_hours, Decimal('7.00'))
        self.assertEqual(res.late_minutes, 0)
        self.assertEqual(res.attendance_status, 'Present')

    def test_overnight_shift_crossover(self):
        from backend.apps.hr.models.attendance import AttendanceShift
        from backend.apps.hr.services.calculations import AttendanceCalculationEngineV1
        
        night_shift = AttendanceShift.objects.create(
            tenant=self.tenant,
            name="Night Shift",
            code="NIGHT",
            start_time=time(22, 0),
            end_time=time(6, 0),
            grace_minutes=10,
            minimum_hours=Decimal('4.00'),
            overtime_after=Decimal('7.00'),
            overnight_shift=True
        )
        
        in_dt = datetime(2026, 1, 1, 22, 0)
        out_dt = datetime(2026, 1, 2, 6, 0) # Next day check out
        
        res = AttendanceCalculationEngineV1.calculate(
            check_in_dt=in_dt,
            check_out_dt=out_dt,
            shift=night_shift
        )
        self.assertEqual(res.total_hours, Decimal('8.00'))
        self.assertEqual(res.overtime_hours, Decimal('1.00')) # 8 - 7 = 1
        self.assertEqual(res.attendance_status, 'Present')

    def test_lateness_grace_period(self):
        from backend.apps.hr.services.calculations import AttendanceCalculationEngineV1
        
        # Within grace period: 09:10 (grace is 15 minutes)
        in_dt = datetime(2026, 1, 1, 9, 10)
        out_dt = datetime(2026, 1, 1, 17, 0)
        
        res = AttendanceCalculationEngineV1.calculate(
            check_in_dt=in_dt,
            check_out_dt=out_dt,
            shift=self.shift
        )
        self.assertEqual(res.late_minutes, 0)
        self.assertEqual(res.attendance_status, 'Present')
        
        # Outside grace period: 09:20
        in_dt2 = datetime(2026, 1, 1, 9, 20)
        res2 = AttendanceCalculationEngineV1.calculate(
            check_in_dt=in_dt2,
            check_out_dt=out_dt,
            shift=self.shift
        )
        self.assertEqual(res2.late_minutes, 20)
        self.assertEqual(res2.attendance_status, 'Late')

    def test_geofencing_validation(self):
        from backend.apps.hr.models.attendance import AttendanceShift
        from backend.apps.hr.services.attendance import AttendanceService
        
        geofenced_shift = AttendanceShift.objects.create(
            tenant=self.tenant,
            name="HQ Office",
            code="HQ",
            start_time=time(9, 0),
            end_time=time(17, 0),
            allowed_latitude=Decimal('6.5244'),
            allowed_longitude=Decimal('3.3792'),
            allowed_radius_meters=100
        )
        
        # Clock in close to HQ (distance < 100 meters)
        in_dt = timezone.now().replace(hour=9, minute=0, second=0, microsecond=0)
        
        # Valid close check-in
        record = AttendanceService.clock_in(
            self.employee, in_dt, gps_lat=Decimal('6.5243'), gps_lon=Decimal('3.3791')
        )
        self.assertIsNotNone(record)
        
        # Reject far check-in (outside 100m)
        with self.assertRaises(ValidationError):
            AttendanceService.clock_in(
                self.employee, in_dt, gps_lat=Decimal('6.6000'), gps_lon=Decimal('3.4000')
            )

    def test_adjustment_approval_recalculation(self):
        from backend.apps.hr.services.attendance import AttendanceService
        from backend.apps.hr.models.attendance import AttendanceRecord, AttendanceAdjustment
        
        # Create Absent record
        today = date(2026, 1, 1)
        record = AttendanceRecord.objects.create(
            tenant=self.tenant,
            employee=self.employee,
            attendance_date=today,
            attendance_status='Absent'
        )
        
        # Request adjustment
        adj = AttendanceAdjustment.objects.create(
            tenant=self.tenant,
            attendance_record=record,
            reason="Forgot to check in",
            requested_by=self.employee,
            adjusted_check_in=time(9, 0),
            adjusted_check_out=time(17, 0)
        )
        
        # Supervisor approvals -> status transitions
        AttendanceService.approve_adjustment(self.tenant, adj.id, supervisor=self.employee, action='approve')
        adj.refresh_from_db()
        self.assertEqual(adj.approval_status, 'Supervisor Approved')
        
        # HR approval -> final recalculated metrics applied
        AttendanceService.approve_adjustment(self.tenant, adj.id, hr=self.employee, action='approve')
        adj.refresh_from_db()
        self.assertEqual(adj.approval_status, 'HR Approved')
        
        record.refresh_from_db()
        self.assertEqual(record.check_in, time(9, 0))
        self.assertEqual(record.check_out, time(17, 0))
        self.assertEqual(record.attendance_status, 'Present')

    def test_payroll_attendance_summary_integration(self):
        from backend.apps.hr.services.attendance import AttendanceService
        from backend.apps.hr.models.attendance import AttendanceRecord
        from backend.apps.hr.services.payroll import PayrollService
        from backend.apps.hr.models.payroll import PayrollPeriod, SalaryStructure, PayrollAccountingConfiguration, PayrollGLAccount, PayrollPayslip
        
        # Setup clean attendance record
        today = date(2026, 1, 1)
        record = AttendanceRecord.objects.create(
            tenant=self.tenant,
            employee=self.employee,
            attendance_date=today,
            check_in=time(9, 0),
            check_out=time(17, 0),
            total_hours=Decimal('7.00'),
            attendance_status='Present',
            shift=self.shift
        )
        
        # Setup payroll configuration
        gl_exp = PayrollGLAccount.objects.create(tenant=self.tenant, code="SAL_EXP", name="Salary Expense")
        gl_paye = PayrollGLAccount.objects.create(tenant=self.tenant, code="PAYE", name="PAYE Liability")
        gl_pen = PayrollGLAccount.objects.create(tenant=self.tenant, code="PEN", name="Pension Liability")
        gl_net = PayrollGLAccount.objects.create(tenant=self.tenant, code="NET", name="Bank Net Salary Liability")
        gl_nhf = PayrollGLAccount.objects.create(tenant=self.tenant, code="NHF", name="NHF Liability")
        
        PayrollAccountingConfiguration.objects.create(
            tenant=self.tenant,
            salary_expense_account=gl_exp,
            paye_liability_account=gl_paye,
            pension_liability_account=gl_pen,
            net_salary_liability_account=gl_net,
            nhf_liability_account=gl_nhf
        )
        
        SalaryStructure.objects.create(
            tenant=self.tenant,
            grade="Grade_A",
            base_salary=Decimal('100000.00'),
            housing_allowance=Decimal('20000.00'),
            transport_allowance=Decimal('10000.00'),
            other_allowances=Decimal('5000.00')
        )
        
        period = PayrollPeriod.objects.create(
            tenant=self.tenant,
            name="January Period",
            start_date=today,
            end_date=today
        )
        
        # Run payroll generation
        run = PayrollService.generate_payroll_run(self.tenant, period.id)
        
        # Check generated payslip matches the attendance summary
        payslip = PayrollPayslip.objects.get(payroll_run=run, employee=self.employee)
        self.assertEqual(payslip.working_days, 1)
        self.assertEqual(payslip.absent_days, 0)
        self.assertEqual(payslip.late_minutes, 0)


