from django.urls import path, include
from backend.apps.tenants.views_web import OnboardWizardWebView, TenantDashboardWebView, SwitchSchoolView
from backend.apps.tenants.views_admin import PlatformSaaSAnalyticsView

urlpatterns = [
    # Web views
    path('onboard/', OnboardWizardWebView.as_view(), name='onboard_wizard'),
    path('tenant-dashboard/', TenantDashboardWebView.as_view(), name='tenant_dashboard_web'),
    path('switch-school/', SwitchSchoolView.as_view(), name='switch_school_web'),
    path('saas-analytics/', PlatformSaaSAnalyticsView.as_view(), name='saas_analytics_web'),
    
    # API views
    path('api/v1/', include('backend.apps.tenants.api.urls')),
]
