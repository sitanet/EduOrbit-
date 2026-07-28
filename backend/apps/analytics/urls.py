from django.urls import path, include
from django.views.generic import RedirectView
from backend.apps.analytics.views_web import ExecutiveDashboardWebView, ReportBuilderWebView

urlpatterns = [
    # Root redirect to dashboard
    path('', RedirectView.as_view(url='dashboard/', permanent=False)),
    # Web views
    path('dashboard/', ExecutiveDashboardWebView.as_view(), name='executive_dashboard_web'),
    path('builder/', ReportBuilderWebView.as_view(), name='report_builder_web'),
    
    # API endpoints versions
    path('api/v1/', include('backend.apps.analytics.api.urls')),
]
