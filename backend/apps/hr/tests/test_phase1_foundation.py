import datetime
from django.test import TestCase
from backend.apps.tenants.models import Tenant
from backend.apps.people.models import Person
from backend.apps.hr.models import EmployeeProfile, JobPosition, CompensationHistory, ContractHistory, OrgAssignmentHistory
from backend.apps.hr.services.employee_number import EmployeeNumberGeneratorService

class Phase1FoundationTestCase(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Academy")
        self.person = Person.objects.create(
            tenant=self.tenant,
            person_number="PER-001",
            first_name="Jane",
            last_name="Doe",
            date_of_birth="1990-01-01",
            gender="female"
        )

    def test_employee_number_generator(self):
        emp_num1 = EmployeeNumberGeneratorService.generate(self.tenant, pattern="SCH-{YEAR}-{SEQ:5}")
        self.assertTrue(emp_num1.startswith("SCH-2026-0000"))

    def test_employee_lifecycle_status_and_7tier_org(self):
        profile = EmployeeProfile.objects.create(
            tenant=self.tenant,
            person=self.person,
            employee_number="SCH-2026-00001",
            job_title="Senior Science Lecturer",
            lifecycle_status="active",
            company_name="EduOrbit Group",
            campus_name="Main Campus",
            division_name="Academics Division",
            directorate_name="STEM Directorate",
            department_name="Biological Sciences",
            unit_name="Lab Unit",
            team_name="Bio Team A",
            cost_centre="CC-201-BIO"
        )
        self.assertEqual(profile.lifecycle_status, "active")
        self.assertEqual(profile.campus_name, "Main Campus")
        self.assertEqual(profile.cost_centre, "CC-201-BIO")

    def test_job_position_headcount(self):
        pos = JobPosition.objects.create(
            tenant=self.tenant,
            title="Vice Principal",
            code="POS-VP-01",
            max_headcount=2,
            filled_headcount=1
        )
        self.assertEqual(pos.vacant_headcount, 1)

    def test_compensation_and_contract_history(self):
        person2 = Person.objects.create(
            tenant=self.tenant,
            person_number="PER-002",
            first_name="John",
            last_name="Smith",
            date_of_birth="1985-05-05",
            gender="male"
        )
        profile = EmployeeProfile.objects.create(
            tenant=self.tenant,
            person=person2,
            employee_number="SCH-2026-00002",
            job_title="Physics Teacher"
        )
        comp = CompensationHistory.objects.create(
            tenant=self.tenant,
            employee=profile,
            base_salary=350000.00,
            currency_code="NGN",
            salary_grade="grade_5"
        )
        self.assertEqual(comp.base_salary, 350000.00)

        contract = ContractHistory.objects.create(
            tenant=self.tenant,
            employee=profile,
            contract_type="permanent"
        )
        self.assertEqual(contract.contract_type, "permanent")
