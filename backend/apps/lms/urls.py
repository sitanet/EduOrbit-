from django.urls import path, include
from django.views.generic import RedirectView
from backend.apps.lms.views_web import LMSDashboardWebView, ModuleBuilderWebView

urlpatterns = [
    # Root redirect to dashboard
    path('', RedirectView.as_view(url='dashboard/', permanent=False)),
    # Web views
    path('dashboard/', LMSDashboardWebView.as_view(), name='lms_dashboard_web'),
    path('builder/', ModuleBuilderWebView.as_view(), name='module_builder_web'),
    
    # API endpoints versions
    path('api/v1/', include('backend.apps.lms.api.urls')),
]
