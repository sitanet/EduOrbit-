from django.urls import path, include
from backend.apps.administration.views_web import PlatformDashboardWebView, SchoolSettingsWebView

urlpatterns = [
    # Web views
    path('dashboard/', PlatformDashboardWebView.as_view(), name='platform_dashboard_web'),
    path('settings/', SchoolSettingsWebView.as_view(), name='school_settings_web'),
    
    # API endpoints versions
    path('api/v1/', include('backend.apps.administration.api.urls')),
]
