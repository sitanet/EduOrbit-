from django.urls import path, include
from backend.apps.admissions.views_web import AdmissionsWizardWebView, AdmissionsDashboardWebView, AdmissionsApplicationCreateWebView, AdmissionsApplicationReviewWebView

urlpatterns = [
    # Web views
    path('wizard/', AdmissionsWizardWebView.as_view(), name='admissions_wizard'),
    path('dashboard/', AdmissionsDashboardWebView.as_view(), name='admissions_dashboard_web'),
    path('application/new/', AdmissionsApplicationCreateWebView.as_view(), name='admissions_application_new'),
    path('<uuid:application_id>/review/', AdmissionsApplicationReviewWebView.as_view(), name='admissions_application_review'),
    
    # API endpoints versions
    path('api/v1/', include('backend.apps.admissions.api.urls')),
]
