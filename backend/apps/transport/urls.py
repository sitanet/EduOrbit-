from django.urls import path, include
from backend.apps.transport.views_web import TransportDashboardWebView, RoutesPlannerWebView

urlpatterns = [
    # Web views
    path('dashboard/', TransportDashboardWebView.as_view(), name='transport_dashboard_web'),
    path('routes/', RoutesPlannerWebView.as_view(), name='routes_planner_web'),
    
    # API endpoints versions
    path('api/v1/', include('backend.apps.transport.api.urls')),
]
