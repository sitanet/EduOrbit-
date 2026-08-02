from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from backend.apps.tenants.models import Tenant, School
from backend.apps.people.models import Person, StudentProfile
from backend.apps.academic.services import GradeCalculationService

class AssessmentPhase4TestCase(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Assessment Tenant")
        self.school = School.objects.create(tenant=self.tenant, name="Excellence College")
        self.person = Person.objects.create(
            tenant=self.tenant,
            person_number="PER-ASM-505",
            first_name="Diana",
            last_name="Prince",
            date_of_birth="2010-04-12",
            gender="female"
        )
        self.student = StudentProfile.objects.create(
            tenant=self.tenant,
            person=self.person,
            student_number="STU-2026-00999",
            admission_number="ADM-00999",
            current_school=self.school
        )
        self.client = APIClient()

    def test_grade_calculation_and_result_computation(self):
        # 1. Single score grading test
        grade_info = GradeCalculationService.calculate_grade(self.school, 75.5)
        self.assertEqual(grade_info["grade_letter"], "A")
        self.assertEqual(grade_info["gpa_value"], 4.0)

        # 2. Term result computation
        scores_data = [
            {"subject_name": "Mathematics", "ca_score": 30, "exam_score": 55, "credit_units": 4},
            {"subject_name": "English", "ca_score": 25, "exam_score": 40, "credit_units": 3}
        ]
        res = GradeCalculationService.compute_student_result(self.student, self.school, scores_data)
        self.assertEqual(res["student_number"], self.student.student_number)
        self.assertEqual(res["overall_average"], 75.0)
        self.assertEqual(res["gpa"], 3.57)

    def test_assessment_calculate_api(self):
        url = '/academic/api/v1/assessment/calculate/'
        payload = {
            "student_id": str(self.student.id),
            "school_id": str(self.school.id),
            "subject_scores": [
                {"subject_name": "Physics", "ca_score": 28, "exam_score": 50, "credit_units": 3}
            ]
        }
        resp = self.client.post(url, payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["status"], "success")
        self.assertEqual(resp.data["data"]["overall_average"], 78.0)
