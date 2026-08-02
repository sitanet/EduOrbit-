from django.urls import path
from backend.apps.ai.api.views import (
    AIChatAPIView, AIGenerateAPIView, AISummarizeAPIView, AIKnowledgeUploadAPIView,
    AIProviderListAPIView, AIUsageAPIView, AIPredictAPIView
)

app_name = 'ai_api'

urlpatterns = [
    path('chat/', AIChatAPIView.as_view(), name='ai_chat'),
    path('generate/', AIGenerateAPIView.as_view(), name='ai_generate'),
    path('summarize/', AISummarizeAPIView.as_view(), name='ai_summarize'),
    path('knowledge/upload/', AIKnowledgeUploadAPIView.as_view(), name='ai_knowledge_upload'),
    path('providers/', AIProviderListAPIView.as_view(), name='ai_providers'),
    path('usage/', AIUsageAPIView.as_view(), name='ai_usage'),
    path('predict/', AIPredictAPIView.as_view(), name='ai_predict'),
]
