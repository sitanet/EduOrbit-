from django.urls import path
from backend.apps.clinic.api.views import (
    PatientProfileAPIView, AppointmentAPIView, ClinicVisitAPIView
)

app_name = 'clinic_api'

urlpatterns = [
    path('patients/', PatientProfileAPIView.as_view(), name='patients'),
    path('appointments/', AppointmentAPIView.as_view(), name='appointments'),
    path('visits/', ClinicVisitAPIView.as_view(), name='visits'),
]
