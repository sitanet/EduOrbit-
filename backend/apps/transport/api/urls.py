from django.urls import path
from backend.apps.transport.api.views import (
    RouteListAPIView, VehicleListAPIView, StudentCheckInAPIView, TransportPaymentAPIView
)

app_name = 'transport_api'

urlpatterns = [
    path('routes/', RouteListAPIView.as_view(), name='route_list'),
    path('vehicles/', VehicleListAPIView.as_view(), name='vehicle_list'),
    path('check-in/', StudentCheckInAPIView.as_view(), name='student_checkin'),
    path('payments/', TransportPaymentAPIView.as_view(), name='transport_payment'),
]
