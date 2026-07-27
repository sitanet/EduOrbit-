from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from backend.apps.tenants.models import School
from backend.apps.identity.models import User
from backend.apps.ai.models import AIMessage, AITokenUsage, KnowledgeDocument
from backend.apps.ai.services.copilot import (
    EduOrbitCopilotService, HRSkillsService, SISSkillsService, FinanceSkillsService,
    LMSSkillsService, CBTSkillsService, CommunicationSkillsService, RAGKnowledgeService
)

class AIChatAPIView(APIView):
    def post(self, request):
        user_id = request.data.get('user_id')
        prompt = request.data.get('prompt')
        copilot_role = request.data.get('copilot_role', 'Principal')
        provider_name = request.data.get('provider_name', 'Gemini')

        try:
            user = User.objects.get(id=user_id)
            res = EduOrbitCopilotService.chat(user=user, prompt=prompt, copilot_role=copilot_role, provider_name=provider_name)
            return Response({"status": "success", "data": res}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AIGenerateAPIView(APIView):
    def post(self, request):
        prompt = request.data.get('prompt', '')
        res = EduOrbitCopilotService.generate(prompt=prompt)
        return Response({"status": "success", "data": res}, status=status.HTTP_200_OK)


class AISummarizeAPIView(APIView):
    def post(self, request):
        text = request.data.get('text', '')
        res = EduOrbitCopilotService.summarize(text=text)
        return Response({"status": "success", "data": res}, status=status.HTTP_200_OK)


class AIKnowledgeUploadAPIView(APIView):
    def post(self, request):
        school_id = request.data.get('school_id')
        document_name = request.data.get('document_name')
        text_content = request.data.get('text_content')

        try:
            school = School.objects.get(id=school_id)
            res = RAGKnowledgeService.upload_document(school=school, document_name=document_name, text_content=text_content)
            return Response({"status": "success", "data": res}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AIProviderListAPIView(APIView):
    def get(self, request):
        providers = [
            {"name": "Google Gemini", "model": "gemini-1.5-pro", "status": "active"},
            {"name": "OpenAI", "model": "gpt-4o", "status": "active"},
            {"name": "Anthropic Claude", "model": "claude-3-5-sonnet", "status": "active"},
            {"name": "DeepSeek", "model": "deepseek-coder-v2", "status": "active"},
            {"name": "Local LLM", "model": "llama-3-8b", "status": "active"}
        ]
        return Response({"status": "success", "count": len(providers), "data": providers})


class AIUsageAPIView(APIView):
    def get(self, request):
        total_tokens = sum(m.prompt_tokens + m.completion_tokens for m in AITokenUsage.objects.all())
        return Response({"status": "success", "data": {"total_calls": AITokenUsage.objects.count(), "total_tokens_consumed": total_tokens}})
