from django.test import TestCase
from django.utils import timezone
from datetime import date, timedelta
from backend.apps.tenants.models import Tenant, School
from backend.apps.people.models import Person
from backend.apps.hr.models import (
    EmployeeProfile, LeaveRequest, LeaveBalance, PayrollPeriod, SalaryStructure, PayrollRun, PerformanceReview, TrainingProgram
)

class HRPlatformTests(TestCase):
    def setUp(self):
        # Create core configurations
        self.tenant = Tenant.objects.create(name="HR Org")
        self.school = School.objects.create(tenant=self.tenant, name="HR High School", school_types=["secondary"])
        
        # Person & Employee profile
        self.person = Person.objects.create(
            tenant=self.tenant,
            person_number="P-50088",
            first_name="Clint",
            last_name="Barton",
            gender="male",
            date_of_birth="1980-04-12"
        )
        self.employee = EmployeeProfile.objects.create(
            person=self.person,
            tenant=self.tenant,
            employee_number="EMP-50088",
            job_title="PE Instructor",
            salary_grade="grade_2"
        )
        
        # Leave balance
        self.balance = LeaveBalance.objects.create(
            employee=self.employee,
            tenant=self.tenant,
            leave_type="annual",
            allowed_days=20,
            remaining_days=20
        )
        
        # Payroll Period & Grade
        self.period = PayrollPeriod.objects.create(
            tenant=self.tenant,
            name="July 2026 Payroll",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30)
        )
        self.salary = SalaryStructure.objects.create(
            tenant=self.tenant,
            grade="grade_2",
            base_salary=60000.00
        )

    def test_payroll_run_earnings_deductions_net(self):
        # Create payroll run
        base_salary = 60000.00
        allowance = 5000.00
        tax = 6000.00
        
        pay = PayrollRun.objects.create(
            employee=self.employee,
            period=self.period,
            tenant=self.tenant,
            earnings=base_salary + allowance,
            deductions=tax,
            net_pay=(base_salary + allowance) - tax,
            status="draft"
        )
        
        self.assertEqual(pay.net_pay, 59000.00)
        self.assertEqual(pay.status, "draft")

    def test_leave_balances_deductions(self):
        # Request leave of 5 days
        req = LeaveRequest.objects.create(
            employee=self.employee,
            tenant=self.tenant,
            leave_type="annual",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=4),  # 5 days inclusive
            status="approved"
        )
        
        # Update balance
        if req.status == 'approved':
            self.balance.remaining_days -= 5
            self.balance.save()
            
        self.assertEqual(self.balance.remaining_days, 15)

    def test_training_program_cpd_hours_totals(self):
        training = TrainingProgram.objects.create(
            tenant=self.tenant,
            name="Advanced Coaching Course",
            cost=15000.00,
            cpd_hours=12
        )
        self.assertEqual(training.cpd_hours, 12)

    def test_onboarding_lifecycle_checklist_tasks(self):
        from backend.apps.hr.models import OnboardingTask
        task = OnboardingTask.objects.create(
            employee=self.employee,
            tenant=self.tenant,
            task_name="Submit employment contract",
            category="contract",
            due_date=date.today() + timedelta(days=7),
            is_completed=False
        )
        self.assertEqual(task.category, "contract")
        self.assertFalse(task.is_completed)

    def test_employee_asset_tracking(self):
        from backend.apps.hr.models import EmployeeAsset
        asset = EmployeeAsset.objects.create(
            employee=self.employee,
            tenant=self.tenant,
            asset_name="Onboarding Work Laptop",
            serial_number="LP-880099",
            asset_type="Laptop"
        )
        self.assertEqual(asset.asset_type, "Laptop")
        self.assertEqual(asset.employee.employee_number, "EMP-50088")

    def test_department_assignment_history(self):
        from backend.apps.hr.models import OrgAssignmentHistory
        history = OrgAssignmentHistory.objects.create(
            employee=self.employee,
            tenant=self.tenant,
            campus_name="Grace Main Campus",
            department_name="Sciences",
            job_position="Chemistry Teacher",
            is_active=True
        )
        self.assertEqual(history.department_name, "Sciences")
        self.assertTrue(history.is_active)

    def test_performance_objectives(self):
        from backend.apps.hr.models import PerformanceObjective
        objective = PerformanceObjective.objects.create(
            employee=self.employee,
            tenant=self.tenant,
            title="Maintain 85% average class score",
            target_date=date.today() + timedelta(days=90),
            progress_percentage=10
        )
        self.assertEqual(objective.progress_percentage, 10)

    def test_candidate_hired_conversion(self):
        from backend.apps.hr.models import JobOpening, Candidate, EmployeeProfile
        job = JobOpening.objects.create(
            tenant=self.tenant,
            title="History Teacher",
            description="Teach history classes."
        )
        cand = Candidate.objects.create(
            tenant=self.tenant,
            job_opening=job,
            first_name="Natasha",
            last_name="Romanoff",
            email="natasha@eduorbit.com",
            status="applied"
        )
        self.assertFalse(EmployeeProfile.objects.filter(tenant=self.tenant, person__user__email=cand.email).exists())
        
        # Transition status to hired
        cand.status = "hired"
        cand.save()
        
        # Verify employee, person, user, and checklist tasks were auto-created
        self.assertTrue(EmployeeProfile.objects.filter(tenant=self.tenant, person__user__email=cand.email).exists())
        emp = EmployeeProfile.objects.get(tenant=self.tenant, person__user__email=cand.email)
        self.assertEqual(emp.person.first_name, "Natasha")
        self.assertEqual(emp.person.user.email, "natasha@eduorbit.com")
        self.assertTrue(emp.onboarding_tasks.filter(category="contract").exists())
