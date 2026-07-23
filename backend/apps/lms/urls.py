from django.urls import path, include
from backend.apps.lms.views_web import LMSDashboardWebView, ModuleBuilderWebView

urlpatterns = [
    # Web views
    path('dashboard/', LMSDashboardWebView.as_view(), name='lms_dashboard_web'),
    path('builder/', ModuleBuilderWebView.as_view(), name='module_builder_web'),
    
    # API endpoints versions
    path('api/v1/', include('backend.apps.lms.api.urls')),
]
