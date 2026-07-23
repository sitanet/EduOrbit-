from django.urls import path, include
from backend.apps.ai.views_web import AIWorkspaceWebView, PromptLibraryWebView

urlpatterns = [
    # Web views
    path('workspace/', AIWorkspaceWebView.as_view(), name='ai_workspace_web'),
    path('prompts/', PromptLibraryWebView.as_view(), name='prompt_library_web'),
    
    # API endpoints versions
    path('api/v1/', include('backend.apps.ai.api.urls')),
]
