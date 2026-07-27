from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from backend.apps.tenants.models import Tenant, School
from backend.apps.academic.models import Subject, Curriculum
from backend.apps.people.models import Person, StudentProfile
from backend.apps.lms.models import Course, Quiz
from backend.apps.eae.models import Question, QuestionChoice, Assessment, AssessmentAttempt, AttemptAnswer, AssessmentResult
from backend.apps.eae.services.cbt import QuestionBankService, ExaminationService, CandidateService, AutoMarkingService, ResultService

class CBTV190TestCase(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test CBT v190 Tenant")
        self.school = School.objects.create(tenant=self.tenant, name="Saint Augustine Science Academy")
        self.curriculum = Curriculum.objects.create(name="Advanced Physics Curriculum", code="PHY-V190")
        self.subject = Subject.objects.create(tenant=self.tenant, school=self.school, curriculum=self.curriculum, name="Physics", code="PHY101")
        self.course = Course.objects.create(tenant=self.tenant, school=self.school, subject=self.subject, title="Classical Mechanics")
        self.lms_quiz = Quiz.objects.create(tenant=self.tenant, course=self.course, title="Newtonian Laws Quiz", total_marks=100)
        
        self.question = Question.objects.create(
            tenant=self.tenant, school=self.school, subject=self.subject, topic="Kinematics", question_text="What is the unit of Acceleration?", question_type="mcq"
        )
        self.choice1 = QuestionChoice.objects.create(tenant=self.tenant, question=self.question, choice_text="m/s^2", is_correct=True)
        self.choice2 = QuestionChoice.objects.create(tenant=self.tenant, question=self.question, choice_text="m/s", is_correct=False)
        
        self.exam = Assessment.objects.create(
            tenant=self.tenant, school=self.school, lms_quiz=self.lms_quiz, title="Physics Final CBT Exam", duration_minutes=60, is_active=True
        )
        
        self.student_person = Person.objects.create(
            tenant=self.tenant, person_number="PER-STU-1900", first_name="Isaac", last_name="Newton", date_of_birth="1643-01-04", gender="male"
        )
        self.student = StudentProfile.objects.create(
            tenant=self.tenant, person=self.student_person, student_number="STU-PHY-001", admission_number="ADM-PHY-001", current_school=self.school
        )
        self.client = APIClient()

    def test_cbt_v190_services_and_lms_reuse(self):
        # 1. Verify LMS Quiz Integration
        self.assertEqual(self.exam.lms_quiz.title, "Newtonian Laws Quiz")

        # 2. Candidate Exam Start
        start_res = CandidateService.start_exam(student=self.student, assessment=self.exam)
        self.assertEqual(start_res["status"], "success")

        # 3. Candidate Submission & Auto-Marking
        attempt = AssessmentAttempt.objects.get(id=start_res["attempt_id"])
        AttemptAnswer.objects.create(tenant=self.tenant, attempt=attempt, question=self.question, selected_choice=self.choice1)
        
        grade_res = AutoMarkingService.auto_grade_attempt(attempt=attempt)
        self.assertEqual(grade_res["status"], "success")
        self.assertEqual(grade_res["percentage"], 100.0)

        # 4. Result Publishing & Notification
        pub_res = ResultService.publish_results(assessment=self.exam)
        self.assertEqual(pub_res["status"], "success")

    def test_cbt_v190_api_endpoints(self):
        # 1. Exams List API
        ex_url = '/eae/api/v1/exams/'
        ex_resp = self.client.get(ex_url)
        self.assertEqual(ex_resp.status_code, status.HTTP_200_OK)

        # 2. Start Exam API
        st_url = '/eae/api/v1/start/'
        payload = {
            "student_id": str(self.student.id),
            "exam_id": str(self.exam.id)
        }
        st_resp = self.client.post(st_url, payload, format='json')
        self.assertEqual(st_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(st_resp.data["status"], "success")
