from django.urls import path, include
from django.views.generic import RedirectView
from backend.apps.transport.views_web import (
    TransportDashboardWebView,
    RoutesPlannerWebView,
    VehiclesFleetWebView,
    DriversDirectoryWebView,
    PassengersManifestWebView,
    VehicleMaintenanceWebView,
    TransportReportsWebView,
)

urlpatterns = [
    # Root redirect to dashboard
    path('', RedirectView.as_view(url='dashboard/', permanent=False)),

    # Web views
    path('dashboard/', TransportDashboardWebView.as_view(), name='transport_dashboard_web'),
    path('routes/', RoutesPlannerWebView.as_view(), name='routes_planner_web'),
    path('vehicles/', VehiclesFleetWebView.as_view(), name='vehicles_fleet_web'),
    path('drivers/', DriversDirectoryWebView.as_view(), name='drivers_directory_web'),
    path('dr/', DriversDirectoryWebView.as_view(), name='drivers_directory_alias_web'),  # alias for /transport/dr
    path('passengers/', PassengersManifestWebView.as_view(), name='passengers_manifest_web'),
    path('maintenance/', VehicleMaintenanceWebView.as_view(), name='vehicle_maintenance_web'),
    path('reports/', TransportReportsWebView.as_view(), name='transport_reports_web'),

    # API endpoints versions
    path('api/v1/', include('backend.apps.transport.api.urls')),
]
