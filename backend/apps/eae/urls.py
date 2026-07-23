from django.urls import path, include
from backend.apps.eae.views_web import EAEDashboardWebView, CBTAttemptWebView

urlpatterns = [
    # Web views
    path('dashboard/', EAEDashboardWebView.as_view(), name='eae_dashboard_web'),
    path('attempts/<uuid:attempt_id>/cbt/', CBTAttemptWebView.as_view(), name='cbt_attempt_web'),
    
    # API endpoints versions
    path('api/v1/', include('backend.apps.eae.api.urls')),
]
