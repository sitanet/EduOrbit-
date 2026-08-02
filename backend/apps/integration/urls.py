from django.urls import path, include
from backend.apps.integration.views_web import IntegrationDashboardWebView

urlpatterns = [
    path('', IntegrationDashboardWebView.as_view(), name='integration_dashboard'),
    path('api/v1/', include('backend.apps.integration.api.urls')),
]
