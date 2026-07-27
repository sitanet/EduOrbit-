from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from backend.apps.tenants.models import Tenant, School
from backend.apps.people.models import Person, StudentProfile
from backend.apps.identity.models import User
from backend.apps.ai.providers.base import get_ai_provider, GoogleGeminiProvider, OpenAIProvider
from backend.apps.ai.services.copilot import CopilotService, PredictiveIntelligenceService, AISearchService, AIReportService

class AIV230TestCase(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test AI Tenant")
        self.school = School.objects.create(tenant=self.tenant, name="Stanford Academy of AI")
        self.user = User.objects.create_user(email="principal_ai@stanford.edu", username="principal_ai", password="Password123!")
        
        self.student_person = Person.objects.create(
            tenant=self.tenant, person_number="PER-AI-001", first_name="Alan", last_name="Turing", date_of_birth="1912-06-23", gender="male"
        )
        self.student = StudentProfile.objects.create(
            tenant=self.tenant, person=self.student_person, student_number="STU-AI-001", admission_number="ADM-AI-001", current_school=self.school
        )
        self.client = APIClient()

    def test_ai_providers_copilots_and_predictive_services(self):
        # 1. Provider Abstraction
        gemini = get_ai_provider("Gemini")
        self.setIsInstance = isinstance(gemini, GoogleGeminiProvider)
        res = gemini.generate_response("Analyze student attendance.")
        self.assertEqual(res["status"], "success")

        openai = get_ai_provider("OpenAI")
        self.assertTrue(isinstance(openai, OpenAIProvider))

        # 2. Copilot Service
        chat_res = CopilotService.chat(user=self.user, prompt="Summarize school financial health.", copilot_role="Principal")
        self.assertEqual(chat_res["status"], "success")
        self.assertEqual(chat_res["copilot_role"], "Principal")

        # 3. Predictive Intelligence Service
        pred_res = PredictiveIntelligenceService.predict_student_dropout_risk(student=self.student)
        self.assertEqual(pred_res["status"], "success")
        self.assertIn("probability", pred_res)

        # 4. AI Search Service
        search_res = AISearchService.natural_language_search(query_text="Students absent today")
        self.assertEqual(search_res["status"], "success")

        # 5. AI Report Service
        rpt_res = AIReportService.generate_board_report(school=self.school)
        self.assertEqual(rpt_res["status"], "success")

    def test_ai_platform_api_endpoints(self):
        # 1. Chat API
        chat_url = '/ai/api/v1/chat/'
        payload = {
            "user_id": str(self.user.id),
            "prompt": "What is our enrollment forecast?",
            "copilot_role": "Principal"
        }
        chat_resp = self.client.post(chat_url, payload, format='json')
        self.assertEqual(chat_resp.status_code, status.HTTP_200_OK)

        # 2. Predict API
        pred_url = '/ai/api/v1/predict/'
        pred_payload = {"student_id": str(self.student.id)}
        pred_resp = self.client.post(pred_url, pred_payload, format='json')
        self.assertEqual(pred_resp.status_code, status.HTTP_200_OK)

        # 3. Providers API
        prov_url = '/ai/api/v1/providers/'
        prov_resp = self.client.get(prov_url)
        self.assertEqual(prov_resp.status_code, status.HTTP_200_OK)
        self.assertTrue(prov_resp.data["count"] > 0)
