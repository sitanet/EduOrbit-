from django.urls import path, include
from backend.apps.workflow.views_web import WorkflowDashboardWebView, ApprovalInboxWebView

urlpatterns = [
    # Web views
    path('dashboard/', WorkflowDashboardWebView.as_view(), name='workflow_dashboard_web'),
    path('inbox/', ApprovalInboxWebView.as_view(), name='approval_inbox_web'),
    
    # API endpoints versions
    path('api/v1/', include('backend.apps.workflow.api.urls')),
]
