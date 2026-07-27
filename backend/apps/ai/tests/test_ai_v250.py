from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from backend.apps.tenants.models import Tenant, School
from backend.apps.people.models import Person, StudentProfile
from backend.apps.identity.models import User
from backend.apps.ai.providers.base import AIProviderFactory, ClaudeProvider, DeepSeekProvider
from backend.apps.ai.services.copilot import (
    EduOrbitCopilotService, HRSkillsService, SISSkillsService, FinanceSkillsService,
    LMSSkillsService, CBTSkillsService, CommunicationSkillsService, RAGKnowledgeService
)

class AIV250TestCase(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test AI v250 Tenant")
        self.school = School.objects.create(tenant=self.tenant, name="Oxford Institute of AI")
        self.user = User.objects.create_user(email="copilot_admin@oxford.edu", username="copilot_admin", password="Password123!")
        
        self.student_person = Person.objects.create(
            tenant=self.tenant, person_number="PER-AI-250", first_name="Grace", last_name="Hopper", date_of_birth="1906-12-09", gender="female"
        )
        self.student = StudentProfile.objects.create(
            tenant=self.tenant, person=self.student_person, student_number="STU-AI-250", admission_number="ADM-AI-250", current_school=self.school
        )
        self.client = APIClient()

    def test_ai_v250_provider_factory_and_copilot_skills(self):
        # 1. Provider Abstraction Factory
        claude = AIProviderFactory.get_provider("Claude")
        self.assertTrue(isinstance(claude, ClaudeProvider))

        deepseek = AIProviderFactory.get_provider("DeepSeek")
        self.assertTrue(isinstance(deepseek, DeepSeekProvider))

        # 2. Central Copilot Chat Service
        chat_res = EduOrbitCopilotService.chat(user=self.user, prompt="Draft staff meeting agenda", copilot_role="HR", tenant=self.tenant)
        self.assertEqual(chat_res["status"], "success")

        # 3. Module Skills (HR, SIS, Finance, LMS, CBT, Communication)
        hr_res = HRSkillsService.detect_payroll_anomalies(school=self.school)
        self.assertEqual(hr_res["status"], "success")

        sis_res = SISSkillsService.predict_dropout(student=self.student)
        self.assertEqual(sis_res["status"], "success")

        fin_res = FinanceSkillsService.forecast_cashflow(school=self.school)
        self.assertEqual(fin_res["status"], "success")

        lms_res = LMSSkillsService.generate_quiz_from_lesson("Photosynthesis")
        self.assertEqual(lms_res["status"], "success")

        cbt_res = CBTSkillsService.detect_cheating_patterns(exam_paper=self.student)
        self.assertEqual(cbt_res["status"], "success")

        comm_res = CommunicationSkillsService.draft_announcement("Parent-Teacher Conference")
        self.assertEqual(comm_res["status"], "success")

        # 4. RAG Document Upload & Embedding Service
        rag_res = RAGKnowledgeService.upload_document(school=self.school, document_name="Staff Code of Conduct", text_content="Staff must maintain professionalism at all times.")
        self.assertEqual(rag_res["status"], "success")

    def test_ai_v250_api_endpoints(self):
        # 1. Chat API
        chat_url = '/ai/api/v1/chat/'
        payload = {
            "user_id": str(self.user.id),
            "prompt": "Explain budget variance for Q3",
            "copilot_role": "Finance"
        }
        chat_resp = self.client.post(chat_url, payload, format='json')
        self.assertEqual(chat_resp.status_code, status.HTTP_200_OK)

        # 2. Knowledge Upload API
        k_url = '/ai/api/v1/knowledge/upload/'
        k_payload = {
            "school_id": str(self.school.id),
            "document_name": "Student Handbook 2026",
            "text_content": "Attendance policy requires 90% attendance."
        }
        k_resp = self.client.post(k_url, k_payload, format='json')
        self.assertEqual(k_resp.status_code, status.HTTP_201_CREATED)

        # 3. Usage Statistics API
        u_url = '/ai/api/v1/usage/'
        u_resp = self.client.get(u_url)
        self.assertEqual(u_resp.status_code, status.HTTP_200_OK)
