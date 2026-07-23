from django.urls import path
from backend.apps.attendance.api.views import (
    AttendanceRecordAPIView, AttendanceCorrectionAPIView, OfflineSyncAPIView
)

app_name = 'attendance_api'

urlpatterns = [
    path('records/', AttendanceRecordAPIView.as_view(), name='records'),
    path('corrections/', AttendanceCorrectionAPIView.as_view(), name='corrections'),
    path('sync/', OfflineSyncAPIView.as_view(), name='offline_sync'),
]
