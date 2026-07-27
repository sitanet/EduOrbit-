from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from backend.apps.tenants.models import Tenant, School
from backend.apps.people.models import Person, StudentProfile
from backend.apps.academic.models import EducationLevel, AcademicLevel, AcademicClass
from backend.apps.academic.services.progression import PromotionService, GraduationService, TranscriptService

class PromotionPhase5TestCase(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Progression Tenant")
        self.school = School.objects.create(tenant=self.tenant, name="University Preparatory High")
        self.person = Person.objects.create(
            tenant=self.tenant,
            person_number="PER-PRO-707",
            first_name="Bruce",
            last_name="Wayne",
            date_of_birth="2009-02-19",
            gender="male"
        )
        self.student = StudentProfile.objects.create(
            tenant=self.tenant,
            person=self.person,
            student_number="STU-2026-00888",
            admission_number="ADM-00888",
            current_school=self.school,
            enrollment_status="active"
        )
        self.education_level = EducationLevel.objects.create(
            tenant=self.tenant, school=self.school, name="Senior High", code="sh"
        )
        self.academic_level = AcademicLevel.objects.create(
            tenant=self.tenant, education_level=self.education_level, name="Grade 11", code="g11"
        )
        self.class1 = AcademicClass.objects.create(
            tenant=self.tenant, academic_level=self.academic_level, name="Grade 11 A"
        )
        self.class2 = AcademicClass.objects.create(
            tenant=self.tenant, academic_level=self.academic_level, name="Grade 12 A"
        )
        self.client = APIClient()

    def test_promotion_graduation_services(self):
        # 1. Class Promotion
        promo_res = PromotionService.run_class_promotion(
            student=self.student,
            previous_class=self.class1,
            new_class=self.class2,
            overall_score=78.5
        )
        self.assertEqual(promo_res["status"], "success")
        self.assertTrue(promo_res["is_promoted"])

        # 2. Graduation
        grad_res = GraduationService.evaluate_and_graduate(self.student)
        self.assertEqual(grad_res["status"], "success")
        self.student.refresh_from_db()
        self.assertEqual(self.student.enrollment_status, "graduated")

        # 3. Transcript Generation
        transcript = TranscriptService.generate_transcript(self.student)
        self.assertEqual(transcript["student_number"], self.student.student_number)
        self.assertEqual(transcript["enrollment_status"], "graduated")
        self.assertTrue("VER-TR-" in transcript["verification_code"])

    def test_promotion_and_transcript_apis(self):
        # 1. Promotion API
        promo_url = '/academic/api/v1/promotion/run/'
        payload = {
            "student_id": str(self.student.id),
            "previous_class_id": str(self.class1.id),
            "new_class_id": str(self.class2.id),
            "overall_score": 82.0
        }
        resp = self.client.post(promo_url, payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # 2. Transcript API
        tr_url = f'/academic/api/v1/transcript/{self.student.id}/'
        tr_resp = self.client.get(tr_url)
        self.assertEqual(tr_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(tr_resp.data["data"]["full_name"], "Bruce Wayne")
