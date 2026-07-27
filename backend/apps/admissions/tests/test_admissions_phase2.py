from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from backend.apps.tenants.models import Tenant, School
from backend.apps.people.models import Person, StudentProfile
from backend.apps.academic.models import AcademicYear, EducationLevel, AcademicLevel, AcademicClass
from backend.apps.admissions.models import (
    AdmissionCampaign, AdmissionIntake, Applicant, AdmissionApplication, AdmissionOffer
)
from backend.apps.admissions.services import AdmissionConversionService

class AdmissionsPhase2TestCase(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Admissions Tenant")
        self.school = School.objects.create(tenant=self.tenant, name="Academy Campus")
        self.year = AcademicYear.objects.create(
            tenant=self.tenant,
            school=self.school,
            name="2026/2027",
            code="2026-2027",
            start_date="2026-09-01",
            end_date="2027-07-15"
        )
        self.campaign = AdmissionCampaign.objects.create(
            tenant=self.tenant,
            school=self.school,
            academic_year=self.year,
            name="2026 Primary Admissions",
            start_date="2026-01-01",
            end_date="2026-08-31"
        )
        self.intake = AdmissionIntake.objects.create(
            tenant=self.tenant,
            campaign=self.campaign,
            name="First Batch"
        )
        self.education_level = EducationLevel.objects.create(
            tenant=self.tenant,
            school=self.school,
            name="Primary Education",
            code="primary"
        )
        self.academic_level = AcademicLevel.objects.create(
            tenant=self.tenant,
            education_level=self.education_level,
            name="Primary 1",
            code="primary-1"
        )
        self.academic_class = AcademicClass.objects.create(
            tenant=self.tenant,
            academic_level=self.academic_level,
            name="Basic 1 Gold"
        )

        self.person = Person.objects.create(
            tenant=self.tenant,
            person_number="PER-APP-001",
            first_name="Diana",
            last_name="Prince",
            date_of_birth="2013-03-22",
            gender="female"
        )
        self.applicant = Applicant.objects.create(
            tenant=self.tenant,
            school=self.school,
            person=self.person,
            applicant_number="APP-2026-00001"
        )
        self.application = AdmissionApplication.objects.create(
            tenant=self.tenant,
            intake=self.intake,
            applicant=self.applicant,
            target_level=self.academic_level,
            status="accepted"
        )
        self.client = APIClient()

    def test_admission_conversion_service(self):
        res = AdmissionConversionService.convert_applicant_to_student(
            application=self.application,
            academic_year=self.year,
            academic_class=self.academic_class
        )
        self.assertEqual(res["status"], "success")
        self.assertTrue(res["student_number"].startswith("STU-"))
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, "enrolled")
        
        # Verify StudentProfile created
        student = StudentProfile.objects.get(id=res["student_profile_id"])
        self.assertEqual(student.person.first_name, "Diana")

    def test_applicant_conversion_api(self):
        url = '/admissions/api/v1/applications/convert/'
        payload = {
            "application_id": str(self.application.id),
            "academic_year_id": str(self.year.id),
            "academic_class_id": str(self.academic_class.id)
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")
        self.assertEqual(response.data["message"], "Applicant converted to student successfully.")
