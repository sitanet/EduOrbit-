from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from backend.apps.tenants.models import Tenant, School
from backend.apps.academic.models import Subject, Curriculum
from backend.apps.people.models import Person, StudentProfile
from backend.apps.lms.models import LearningModule, LearningUnit, LearningActivity, StudentProgress, Course
from backend.apps.lms.services.learning import CourseService, AssignmentSubmissionService, GradeSubmissionService

class LMSV190TestCase(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test LMS Tenant")
        self.school = School.objects.create(tenant=self.tenant, name="Academy of Sciences")
        self.curriculum = Curriculum.objects.create(name="STEM Curriculum", code="STEM-001")
        self.subject = Subject.objects.create(tenant=self.tenant, school=self.school, curriculum=self.curriculum, name="Mathematics", code="MTH101")
        self.module = LearningModule.objects.create(tenant=self.tenant, school=self.school, subject=self.subject, title="Algebra & Calculus", topic="Algebra")
        self.unit = LearningUnit.objects.create(tenant=self.tenant, module=self.module, name="Quadratic Equations", order=1)
        self.activity = LearningActivity.objects.create(tenant=self.tenant, unit=self.unit, name="Quadratic Equations Quiz 1", activity_type="assignment")
        
        self.student_person = Person.objects.create(
            tenant=self.tenant, person_number="PER-STU-777", first_name="Albert", last_name="Einstein", date_of_birth="1879-03-14", gender="male"
        )
        self.course = Course.objects.create(tenant=self.tenant, school=self.school, subject=self.subject, title="Advanced Calculus")
        self.student = StudentProfile.objects.create(
            tenant=self.tenant, person=self.student_person, student_number="STU-LMS-001", admission_number="ADM-LMS-001", current_school=self.school
        )
        self.client = APIClient()

    def test_course_authoring_and_submission_services(self):
        # 1. Course Module Creation
        mod_res = CourseService.create_module(school=self.school, subject=self.subject, title="Quantum Mechanics", topic="Physics")
        self.assertEqual(mod_res["status"], "success")

        # 2. Assignment Submission
        sub_res = AssignmentSubmissionService.submit_assignment(student=self.student, activity=self.activity, content_body="My math answer sheet")
        self.assertEqual(sub_res["status"], "success")

        # 3. Grade Submission
        progress = StudentProgress.objects.get(id=sub_res["progress_id"])
        grd_res = GradeSubmissionService.grade_submission(progress=progress, score_percentage=98.50)
        self.assertEqual(grd_res["status"], "success")
        self.assertEqual(grd_res["score"], 98.50)

    def test_lms_api_endpoints(self):
        # 1. Courses API
        c_url = '/lms/api/v1/courses/'
        c_resp = self.client.get(c_url)
        self.assertEqual(c_resp.status_code, status.HTTP_200_OK)
        self.assertTrue(c_resp.data["count"] > 0)

        # 2. Submissions API
        sub_url = '/lms/api/v1/submissions/'
        payload = {
            "student_id": str(self.student.id),
            "activity_id": str(self.activity.id),
            "content_body": "Uploaded PDF work"
        }
        sub_resp = self.client.post(sub_url, payload, format='json')
        self.assertEqual(sub_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(sub_resp.data["status"], "success")
