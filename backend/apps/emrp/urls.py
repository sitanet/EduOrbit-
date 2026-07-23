from django.urls import path, include
from backend.apps.emrp.views_web import EMRPDashboardWebView, BroadsheetWebView

urlpatterns = [
    # Web views
    path('dashboard/', EMRPDashboardWebView.as_view(), name='emrp_dashboard_web'),
    path('exams/<uuid:exam_id>/broadsheet-view/', BroadsheetWebView.as_view(), name='broadsheet_web'),
    
    # API endpoints versions
    path('api/v1/', include('backend.apps.emrp.api.urls')),
]
