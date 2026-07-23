from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from backend.apps.tenants.models import Tenant, School
from backend.apps.academic.models import (
    AcademicYear, EducationLevel, AcademicLevel, AcademicClass,
    Curriculum, Subject, GradingScale, PromotionPolicy
)

class AcademicConfigurationTests(TestCase):
    def setUp(self):
        # Create tenant
        self.tenant = Tenant.objects.create(name="Grace Group")
        
        # Create two separate schools under the same tenant to test isolation
        self.school_primary = School.objects.create(tenant=self.tenant, name="Grace Primary School", school_types=["primary"])
        self.school_college = School.objects.create(tenant=self.tenant, name="Grace College", school_types=["secondary"])
        
    def test_multi_school_configuration_isolation(self):
        # Create active AcademicYear for Primary school
        year_primary = AcademicYear.objects.create(
            school=self.school_primary,
            tenant=self.tenant,
            name="2026/2027 Primary Year",
            code="2026-2027-pri",
            start_date=timezone.now().date(),
            end_date=(timezone.now() + timedelta(days=365)).date(),
            status='active'
        )
        
        # Verify Primary year lists under Primary school
        self.assertEqual(AcademicYear.objects.filter(school=self.school_primary).count(), 1)
        # Verify College school has no academic years configured (complete isolation!)
        self.assertEqual(AcademicYear.objects.filter(school=self.school_college).count(), 0)

    def test_grading_boundaries(self):
        # Create grading scale boundaries for College
        scale_a = GradingScale.objects.create(
            school=self.school_college,
            tenant=self.tenant,
            name="A Excellent",
            min_score=80.0,
            max_score=100.0,
            grade_letter="A",
            gpa_value=4.0
        )
        
        self.assertEqual(scale_a.grade_letter, "A")
        self.assertEqual(float(scale_a.min_score), 80.0)
        self.assertEqual(float(scale_a.max_score), 100.0)

    def test_subject_curriculum_mappings(self):
        # Create global Curriculum
        curriculum = Curriculum.objects.create(
            name="Cambridge Checkpoint 2024",
            code="cambridge-cp-2024",
            version="1.0"
        )
        
        # Create Subject linked to Curriculum in Primary School
        sub_math = Subject.objects.create(
            school=self.school_primary,
            tenant=self.tenant,
            curriculum=curriculum,
            code="maths-p5",
            name="Mathematics Grade 5",
            category="stem"
        )
        
        self.assertEqual(sub_math.category, "stem")
        self.assertEqual(sub_math.curriculum, curriculum)
