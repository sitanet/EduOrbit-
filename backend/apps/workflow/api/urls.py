from django.urls import path
from backend.apps.workflow.api.views import (
    WorkflowInstanceAPIView, WorkflowTaskAPIView, WorkflowApprovalAPIView
)

app_name = 'workflow_api'

urlpatterns = [
    path('instances/', WorkflowInstanceAPIView.as_view(), name='instances'),
    path('tasks/', WorkflowTaskAPIView.as_view(), name='tasks'),
    path('approvals/', WorkflowApprovalAPIView.as_view(), name='approvals'),
]
