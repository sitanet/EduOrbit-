from django.urls import path, include
from django.views.generic import RedirectView
from backend.apps.eae.views_web import EAEDashboardWebView, CBTAttemptWebView

urlpatterns = [
    # Root redirect to dashboard
    path('', RedirectView.as_view(url='dashboard/', permanent=False)),
    # Web views
    path('dashboard/', EAEDashboardWebView.as_view(), name='eae_dashboard_web'),
    path('attempts/<uuid:attempt_id>/cbt/', CBTAttemptWebView.as_view(), name='cbt_attempt_web'),
    
    # API endpoints versions
    path('api/v1/', include('backend.apps.eae.api.urls')),
]
