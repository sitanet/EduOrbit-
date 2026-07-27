from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from backend.apps.tenants.models import Tenant, School
from backend.apps.academic.models import Subject, Curriculum
from backend.apps.people.models import Person, StudentProfile
from backend.apps.eae.models import Question, QuestionChoice, Assessment, AssessmentAttempt, AttemptAnswer, AssessmentResult
from backend.apps.eae.services.cbt import QuestionBankService, ExaminationService, CandidateService, AutoMarkingService, ResultService

class CBTV200TestCase(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test CBT Tenant")
        self.school = School.objects.create(tenant=self.tenant, name="St. Mark Comprehensive College")
        self.curriculum = Curriculum.objects.create(name="National Curriculum", code="NAT-CBT-01")
        self.subject = Subject.objects.create(tenant=self.tenant, school=self.school, curriculum=self.curriculum, name="Chemistry", code="CHM101")
        
        self.question = Question.objects.create(
            tenant=self.tenant, school=self.school, subject=self.subject, topic="Atomic Structure", question_text="What is the atomic number of Carbon?", question_type="mcq"
        )
        self.choice1 = QuestionChoice.objects.create(tenant=self.tenant, question=self.question, choice_text="6", is_correct=True)
        self.choice2 = QuestionChoice.objects.create(tenant=self.tenant, question=self.question, choice_text="12", is_correct=False)
        
        self.exam = Assessment.objects.create(
            tenant=self.tenant, school=self.school, title="Mid-Term Chemistry Examination", duration_minutes=45, is_active=True
        )
        
        self.student_person = Person.objects.create(
            tenant=self.tenant, person_number="PER-STU-9900", first_name="Marie", last_name="Curie", date_of_birth="1867-11-07", gender="female"
        )
        self.student = StudentProfile.objects.create(
            tenant=self.tenant, person=self.student_person, student_number="STU-CBT-001", admission_number="ADM-CBT-001", current_school=self.school
        )
        self.client = APIClient()

    def test_cbt_services_workflow(self):
        # 1. Question Creation via Service
        q_res = QuestionBankService.create_question(
            school=self.school, subject=self.subject, text="Which gas is essential for respiration?",
            choices_data=[{"text": "Oxygen", "is_correct": True}, {"text": "Nitrogen", "is_correct": False}]
        )
        self.assertEqual(q_res["status"], "success")

        # 2. Exam Candidate Start
        start_res = CandidateService.start_exam(student=self.student, assessment=self.exam)
        self.assertEqual(start_res["status"], "success")
        
        attempt = AssessmentAttempt.objects.get(id=start_res["attempt_id"])
        AttemptAnswer.objects.create(
            tenant=self.tenant, attempt=attempt, question=self.question, selected_choice=self.choice1
        )

        # 3. Auto-Grading Engine
        grade_res = AutoMarkingService.auto_grade_attempt(attempt=attempt)
        self.assertEqual(grade_res["status"], "success")
        self.assertEqual(grade_res["percentage"], 100.0)

        # 4. Result Publication Engine
        pub_res = ResultService.publish_results(assessment=self.exam)
        self.assertEqual(pub_res["status"], "success")
        self.assertEqual(pub_res["published_count"], 1)

    def test_cbt_api_endpoints(self):
        # 1. Question Banks API
        qb_url = '/eae/api/v1/question-banks/'
        qb_resp = self.client.get(qb_url)
        self.assertEqual(qb_resp.status_code, status.HTTP_200_OK)
        self.assertTrue(qb_resp.data["count"] > 0)

        # 2. Exams List API
        ex_url = '/eae/api/v1/exams/'
        ex_resp = self.client.get(ex_url)
        self.assertEqual(ex_resp.status_code, status.HTTP_200_OK)

        # 3. Start Exam API
        st_url = '/eae/api/v1/start/'
        payload = {
            "student_id": str(self.student.id),
            "exam_id": str(self.exam.id)
        }
        st_resp = self.client.post(st_url, payload, format='json')
        self.assertEqual(st_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(st_resp.data["status"], "success")
