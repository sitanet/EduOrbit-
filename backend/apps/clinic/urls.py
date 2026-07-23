from django.urls import path, include
from backend.apps.clinic.views_web import ClinicDashboardWebView, ConsultationDeskWebView

urlpatterns = [
    # Web views
    path('dashboard/', ClinicDashboardWebView.as_view(), name='clinic_dashboard_web'),
    path('consultation/', ConsultationDeskWebView.as_view(), name='consultation_desk_web'),
    
    # API endpoints versions
    path('api/v1/', include('backend.apps.clinic.api.urls')),
]
