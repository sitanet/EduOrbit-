from django.urls import path
from backend.apps.transport.api.views import (
    RouteAPIView, TripAPIView, VehicleLocationAPIView
)

app_name = 'transport_api'

urlpatterns = [
    path('routes/', RouteAPIView.as_view(), name='routes'),
    path('trips/', TripAPIView.as_view(), name='trips'),
    path('gps/', VehicleLocationAPIView.as_view(), name='gps'),
]
