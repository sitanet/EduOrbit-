from django.test import TestCase
from backend.apps.tenants.models import Tenant, School
from backend.apps.academic.models import AcademicYear, AcademicPeriod
from backend.apps.academic.services.structure import AcademicStructureService

class AcademicStructureTestCase(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Academic Tenant")
        self.school = School.objects.create(tenant=self.tenant, name="Premier College")
        
        self.year1 = AcademicYear.objects.create(
            tenant=self.tenant,
            school=self.school,
            name="2025/2026",
            code="2025-2026",
            start_date="2025-09-01",
            end_date="2026-07-15",
            status="active"
        )
        self.year2 = AcademicYear.objects.create(
            tenant=self.tenant,
            school=self.school,
            name="2026/2027",
            code="2026-2027",
            start_date="2026-09-01",
            end_date="2027-07-15",
            status="future"
        )
        self.period1 = AcademicPeriod.objects.create(
            tenant=self.tenant,
            academic_year=self.year2,
            name="First Term",
            order=1,
            start_date="2026-09-01",
            end_date="2026-12-15",
            status="future"
        )

    def test_activate_academic_year(self):
        res = AcademicStructureService.activate_academic_year(self.year2)
        self.assertEqual(res["status"], "success")
        self.year1.refresh_from_db()
        self.year2.refresh_from_db()
        self.assertEqual(self.year1.status, "archived")
        self.assertEqual(self.year2.status, "active")

    def test_activate_academic_period(self):
        res = AcademicStructureService.activate_academic_period(self.period1)
        self.assertEqual(res["status"], "success")
        self.period1.refresh_from_db()
        self.assertEqual(self.period1.status, "active")
