from django.urls import path, include
from django.views.generic import RedirectView
from backend.apps.academic.views_web import AcademicWizardWebView, AcademicDashboardWebView, SubjectManagementWebView

urlpatterns = [
    # Root redirect to dashboard
    path('', RedirectView.as_view(url='dashboard/', permanent=False)),
    # Web views
    path('wizard/', AcademicWizardWebView.as_view(), name='academic_wizard'),
    path('dashboard/', AcademicDashboardWebView.as_view(), name='academic_dashboard_web'),
    path('subjects/', SubjectManagementWebView.as_view(), name='subject_management_web'),
    
    # API endpoints versions
    path('api/v1/', include('backend.apps.academic.api.urls')),
]
