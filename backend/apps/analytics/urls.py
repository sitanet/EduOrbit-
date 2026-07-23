from django.urls import path, include
from backend.apps.analytics.views_web import ExecutiveDashboardWebView, ReportBuilderWebView

urlpatterns = [
    # Web views
    path('dashboard/', ExecutiveDashboardWebView.as_view(), name='executive_dashboard_web'),
    path('builder/', ReportBuilderWebView.as_view(), name='report_builder_web'),
    
    # API endpoints versions
    path('api/v1/', include('backend.apps.analytics.api.urls')),
]
