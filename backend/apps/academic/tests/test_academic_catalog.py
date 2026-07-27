from django.test import TestCase
from backend.apps.tenants.models import Tenant, School
from backend.apps.academic.models import (
    AcademicYear, EducationLevel, AcademicLevel, AcademicClass, Curriculum, Subject
)
from backend.apps.academic.services.catalog import AcademicCatalogService

class AcademicCatalogTestCase(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Academic Catalog Tenant")
        self.school = School.objects.create(tenant=self.tenant, name="Science & Arts Academy")
        self.year = AcademicYear.objects.create(
            tenant=self.tenant,
            school=self.school,
            name="2026/2027",
            code="2026-2027",
            start_date="2026-09-01",
            end_date="2027-07-15"
        )
        self.curriculum = Curriculum.objects.create(
            name="Nigerian National Curriculum 2024",
            code="NNC-2024",
            version="1.0.0"
        )
        self.education_level = EducationLevel.objects.create(
            tenant=self.tenant,
            school=self.school,
            name="Senior Secondary",
            code="senior-secondary"
        )
        self.academic_level = AcademicLevel.objects.create(
            tenant=self.tenant,
            education_level=self.education_level,
            name="SS 1",
            code="ss-1"
        )
        self.academic_class = AcademicClass.objects.create(
            tenant=self.tenant,
            academic_level=self.academic_level,
            name="SS 1 Science"
        )

    def test_create_subject_and_class_mapping(self):
        # 1. Create Subject
        sub_res = AcademicCatalogService.create_subject(
            school=self.school,
            curriculum=self.curriculum,
            code="PHYS-101",
            name="Physics 101",
            category="stem",
            credit_units=4
        )
        self.assertEqual(sub_res["status"], "success")
        self.assertEqual(sub_res["credit_units"], 4)
        subject = Subject.objects.get(id=sub_res["subject_id"])

        # 2. Map Subject to Class
        map_res = AcademicCatalogService.map_subject_to_class(
            academic_year=self.year,
            subject=subject,
            academic_class=self.academic_class,
            compulsory=True
        )
        self.assertEqual(map_res["status"], "success")

        # 3. Workload Calculation
        workload = AcademicCatalogService.get_class_curriculum_workload(self.academic_class)
        self.assertEqual(workload["offering_count"], 1)
        self.assertEqual(workload["total_credit_units"], 4)
        self.assertIn("Physics 101", workload["subjects"])
