from django.urls import path, include
from backend.apps.clinic.views_web import (
    ClinicDashboardWebView,
    ConsultationDeskWebView,
    ClinicVisitsWebView,
    ClinicRecordsWebView,
    ClinicInventoryWebView,
    ClinicReportsWebView,
    SickBayWebView,
    PatientSearchJsonView,
)

urlpatterns = [
    # Web views
    path('', ClinicDashboardWebView.as_view(), name='clinic_index_web'),
    path('dashboard/', ClinicDashboardWebView.as_view(), name='clinic_dashboard_web'),
    path('consultation/', ConsultationDeskWebView.as_view(), name='consultation_desk_web'),
    path('visits/', ClinicVisitsWebView.as_view(), name='clinic_visits_web'),
    path('records/', ClinicRecordsWebView.as_view(), name='clinic_records_web'),
    path('inventory/', ClinicInventoryWebView.as_view(), name='clinic_inventory_web'),
    path('reports/', ClinicReportsWebView.as_view(), name='clinic_reports_web'),

    # ── New routes ──────────────────────────────────────────────────────────
    path('sickbay/', SickBayWebView.as_view(), name='clinic_sickbay_web'),
    path('pharmacy/', ClinicInventoryWebView.as_view(), name='clinic_pharmacy_web'),  # alias
    path('patients/search/', PatientSearchJsonView.as_view(), name='patient_search_json'),

    # API endpoints versions
    path('api/v1/', include('backend.apps.clinic.api.urls')),
]
