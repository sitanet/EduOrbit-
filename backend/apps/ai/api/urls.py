from django.urls import path
from backend.apps.ai.api.views import (
    AIConversationAPIView, AIMessageAPIView, PromptTemplateAPIView
)

app_name = 'ai_api'

urlpatterns = [
    path('conversations/', AIConversationAPIView.as_view(), name='conversations'),
    path('messages/', AIMessageAPIView.as_view(), name='messages'),
    path('prompts/', PromptTemplateAPIView.as_view(), name='prompts'),
]
