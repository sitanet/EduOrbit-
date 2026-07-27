from django.urls import path
from backend.apps.integration.api.views import (
    IntegrationProviderListAPIView, WebhookListAPIView, WebhookCreateAPIView,
    WorkflowListAPIView, WorkflowCreateAPIView, JobListAPIView, APIClientListAPIView, EventListAPIView
)

app_name = 'integration_api'

urlpatterns = [
    path('providers/', IntegrationProviderListAPIView.as_view(), name='provider_list'),
    path('webhooks/', WebhookListAPIView.as_view(), name='webhook_list'),
    path('webhooks/create/', WebhookCreateAPIView.as_view(), name='webhook_create'),
    path('workflows/', WorkflowListAPIView.as_view(), name='workflow_list'),
    path('workflows/create/', WorkflowCreateAPIView.as_view(), name='workflow_create'),
    path('jobs/', JobListAPIView.as_view(), name='job_list'),
    path('api-clients/', APIClientListAPIView.as_view(), name='api_client_list'),
    path('events/', EventListAPIView.as_view(), name='event_list'),
]
