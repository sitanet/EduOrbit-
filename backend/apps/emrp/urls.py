from django.urls import path, include
from django.views.generic import RedirectView
from backend.apps.emrp.views_web import EMRPDashboardWebView, BroadsheetWebView, ReportsBroadsheetWebView

urlpatterns = [
    # Root redirect to dashboard
    path('', RedirectView.as_view(url='dashboard/', permanent=False)),
    # Web views
    path('dashboard/', EMRPDashboardWebView.as_view(), name='emrp_dashboard_web'),
    path('reports/', ReportsBroadsheetWebView.as_view(), name='emrp_reports_web'),
    path('exams/<uuid:exam_id>/broadsheet-view/', BroadsheetWebView.as_view(), name='broadsheet_web'),
    
    # API endpoints versions
    path('api/v1/', include('backend.apps.emrp.api.urls')),
]
