from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from backend.apps.tenants.models import Tenant, School
from backend.apps.people.models import Person, StudentProfile
from backend.apps.students.services.student_number import StudentNumberGeneratorService
from backend.apps.students.services.lifecycle import StudentLifecycleService

class SISPhase1StudentFoundationTestCase(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test SIS Phase 1 Tenant")
        self.school = School.objects.create(tenant=self.tenant, name="Saint Jude College")
        self.client = APIClient()

    def test_student_number_generator(self):
        stu_num = StudentNumberGeneratorService.generate_next_student_number(tenant=self.tenant)
        self.assertTrue(stu_num.startswith("STU-"))

    def test_student_enrollment_api(self):
        url = '/students/api/v1/students/enroll/'
        payload = {
            "school_id": str(self.school.id),
            "first_name": "Tony",
            "last_name": "Stark",
            "gender": "male",
            "date_of_birth": "2012-05-29"
        }

        # Attach tenant to request state
        response = self.client.post(url, payload, format='json', HTTP_X_TENANT_ID=str(self.tenant.id))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], "success")
        self.assertEqual(response.data["data"]["name"], "Tony Stark")
        self.assertTrue(response.data["data"]["student_number"].startswith("STU-"))

    def test_student_lifecycle_transition_api(self):
        person = Person.objects.create(
            tenant=self.tenant,
            person_number="PER-STU-999",
            first_name="Bruce",
            last_name="Banner",
            date_of_birth="2011-12-18",
            gender="male"
        )
        profile = StudentProfile.objects.create(
            tenant=self.tenant,
            person=person,
            student_number="STU-2026-00999",
            current_school=self.school,
            enrollment_status="pending"
        )

        url = f'/students/api/v1/students/{profile.id}/transition/'
        payload = {"new_status": "active", "reason": "Admissions Cleared"}
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["new_status"], "active")
        profile.refresh_from_db()
        self.assertEqual(profile.enrollment_status, "active")
