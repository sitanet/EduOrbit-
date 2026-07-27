from django.urls import path
from backend.apps.clinic.api.views import (
    PatientRecordListAPIView, ClinicVisitCreateAPIView, ClinicVisitListAPIView, MedicationAdministerAPIView
)

app_name = 'clinic_api'

urlpatterns = [
    path('records/', PatientRecordListAPIView.as_view(), name='patient_records_list'),
    path('visits/', ClinicVisitListAPIView.as_view(), name='clinic_visits_list'),
    path('visits/create/', ClinicVisitCreateAPIView.as_view(), name='clinic_visit_create'),
    path('medications/administer/', MedicationAdministerAPIView.as_view(), name='medication_administer'),
]
