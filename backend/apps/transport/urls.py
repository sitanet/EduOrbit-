from django.urls import path, include
from django.views.generic import RedirectView
from backend.apps.transport.views_web import TransportDashboardWebView, RoutesPlannerWebView

urlpatterns = [
    # Root redirect to dashboard
    path('', RedirectView.as_view(url='dashboard/', permanent=False)),
    # Web views
    path('dashboard/', TransportDashboardWebView.as_view(), name='transport_dashboard_web'),
    path('routes/', RoutesPlannerWebView.as_view(), name='routes_planner_web'),
    
    # API endpoints versions
    path('api/v1/', include('backend.apps.transport.api.urls')),
]
