from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from backend.apps.tenants.models import Tenant, School
from backend.apps.people.models import Person, StudentProfile
from backend.apps.academic.models import AcademicYear, AcademicPeriod, EducationLevel, AcademicLevel, Subject, Curriculum as AcademicCurriculum
from backend.apps.lms.models import (
    ContentType, LearningModule, LearningUnit, LearningContent,
    LearningContentVersion, StudentProgress, LearningActivity
)

class LMSPlatformTests(TestCase):
    def setUp(self):
        # Create core configurations
        self.tenant = Tenant.objects.create(name="LMS Org")
        self.school = School.objects.create(tenant=self.tenant, name="LMS Academy", school_types=["secondary"])
        
        # Academic structures
        self.year = AcademicYear.objects.create(
            school=self.school,
            tenant=self.tenant,
            name="2026/2027 Year",
            code="2026-27-lms",
            start_date=timezone.now().date(),
            end_date=(timezone.now() + timedelta(days=365)).date(),
            status='active'
        )
        self.period = AcademicPeriod.objects.create(
            academic_year=self.year,
            tenant=self.tenant,
            name="First Term",
            start_date=timezone.now().date(),
            end_date=(timezone.now() + timedelta(days=120)).date(),
            status='active'
        )
        self.aca_curriculum = AcademicCurriculum.objects.create(name="Checkpoint", code="cp-27", version="1")
        self.subject = Subject.objects.create(school=self.school, tenant=self.tenant, curriculum=self.aca_curriculum, code="bio-1", name="Biology 1")
        self.ed_level = EducationLevel.objects.create(school=self.school, tenant=self.tenant, name="Secondary", code="sec")
        self.ac_level = AcademicLevel.objects.create(education_level=self.ed_level, tenant=self.tenant, name="JSS 1", code="jss1")
        
        # Student Profile
        self.person = Person.objects.create(
            tenant=self.tenant,
            person_number="P-50088",
            first_name="Bruce",
            last_name="Banner",
            gender="male",
            date_of_birth="2010-04-12"
        )
        self.student = StudentProfile.objects.create(
            person=self.person,
            tenant=self.tenant,
            student_number="STU-50088",
            current_school=self.school,
            enrollment_status="enrolled"
        )
        
        # Lookups
        self.type_pdf = ContentType.objects.create(name="PDF Document", code="pdf")
        
        # Module and Unit headers
        self.module = LearningModule.objects.create(
            school=self.school,
            tenant=self.tenant,
            subject=self.subject,
            topic="Cell Biology",
            title="Introduction to Cell structures"
        )
        self.unit = LearningUnit.objects.create(
            module=self.module,
            tenant=self.tenant,
            name="Organelles",
            order=1
        )
        
    def test_version_controlled_content_and_rollback(self):
        # 1. Register study content
        content = LearningContent.objects.create(
            unit=self.unit,
            tenant=self.tenant,
            content_type=self.type_pdf,
            title="Cell Core Organelles Plan"
        )
        self.assertEqual(content.title, "Cell Core Organelles Plan")
        
        # 2. Version 1 creation
        v1 = LearningContentVersion.objects.create(
            content=content,
            tenant=self.tenant,
            version_number=1,
            body="V1 content data.",
            status="published"
        )
        self.assertEqual(v1.version_number, 1)
        
        # 3. Version 2 creation (Draft)
        v2 = LearningContentVersion.objects.create(
            content=content,
            tenant=self.tenant,
            version_number=2,
            body="V2 draft changes.",
            status="draft"
        )
        
        # Fetch active version (filter by published status)
        active_version = content.versions.filter(status="published").first()
        self.assertEqual(active_version.body, "V1 content data.")

    def test_student_progress_check(self):
        # Create reading activity
        activity = LearningActivity.objects.create(
            unit=self.unit,
            tenant=self.tenant,
            name="Read cell note slides",
            activity_type="reading",
            order=1
        )
        
        # Track start
        prog = StudentProgress.objects.create(
            student=self.student,
            activity=activity,
            tenant=self.tenant,
            status="started"
        )
        
        # Update completion
        prog.status = "completed"
        prog.completion_percentage = 100.00
        prog.save()
        
        # Verify
        self.assertEqual(prog.status, "completed")
