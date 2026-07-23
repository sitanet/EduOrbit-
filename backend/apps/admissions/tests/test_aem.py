from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from backend.apps.tenants.models import Tenant, School
from backend.apps.people.models import Person, StudentProfile
from backend.apps.academic.models import AcademicYear, EducationLevel, AcademicLevel, AcademicClass
from backend.apps.admissions.models import AdmissionCampaign, AdmissionIntake, Applicant, AdmissionApplication
from backend.apps.admissions.services import EnrollmentService

class AdmissionsEnrollmentTests(TestCase):
    def setUp(self):
        # Create core configurations
        self.tenant = Tenant.objects.create(name="Apex Org")
        self.school = School.objects.create(tenant=self.tenant, name="Apex Secondary", school_types=["secondary"])
        
        # Academic structures
        self.year = AcademicYear.objects.create(
            school=self.school,
            tenant=self.tenant,
            name="2026/2027 Year",
            code="2026-27",
            start_date=timezone.now().date(),
            end_date=(timezone.now() + timedelta(days=365)).date(),
            status='active'
        )
        self.ed_level = EducationLevel.objects.create(school=self.school, tenant=self.tenant, name="Secondary", code="sec")
        self.ac_level = AcademicLevel.objects.create(education_level=self.ed_level, tenant=self.tenant, name="JSS 1", code="jss1")
        self.ac_class = AcademicClass.objects.create(academic_level=self.ac_level, tenant=self.tenant, name="JSS 1 Gold")
        
        # Person profile
        self.person = Person.objects.create(
            tenant=self.tenant,
            person_number="P-10022",
            first_name="Jane",
            last_name="Doe",
            gender="female",
            date_of_birth="2012-08-20"
        )
        
        # Admissions setup
        self.campaign = AdmissionCampaign.objects.create(
            school=self.school,
            tenant=self.tenant,
            academic_year=self.year,
            name="2027 Admissions",
            start_date=timezone.now().date(),
            end_date=(timezone.now() + timedelta(days=90)).date()
        )
        self.intake = AdmissionIntake.objects.create(campaign=self.campaign, tenant=self.tenant, name="Batch A")
        self.applicant = Applicant.objects.create(school=self.school, tenant=self.tenant, person=self.person, applicant_number="APP-10022")
        self.application = AdmissionApplication.objects.create(
            intake=self.intake,
            applicant=self.applicant,
            target_level=self.ac_level,
            tenant=self.tenant,
            status='accepted'
        )
        
    def test_applicant_promoted_to_student_profile(self):
        # Trigger Enrollment Promotion
        student = EnrollmentService.enroll_applicant(
            application_id=self.application.id,
            class_id=self.ac_class.id
        )
        
        # 1. Verify StudentProfile created and linked to Person Doe
        self.assertEqual(student.person, self.person)
        self.assertEqual(student.enrollment_status, "enrolled")
        
        # 2. Verify Application status updated
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, "enrolled")
        
        # 3. Verify PersonRole assignment has student role
        self.assertEqual(self.person.assigned_roles.filter(role="student").count(), 1)
