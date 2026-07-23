from django.urls import path
from backend.apps.timetable.api.views import (
    ResourceAPIView, ResourceDetailAPIView,
    ScheduleAPIView, ScheduleDetailAPIView,
    ConflictReportAPIView
)

app_name = 'timetable_api'

urlpatterns = [
    path('schedules/resources/', ResourceAPIView.as_view(), name='resources'),
    path('schedules/resources/<int:pk>/', ResourceDetailAPIView.as_view(), name='resource_detail'),
    path('schedules/', ScheduleAPIView.as_view(), name='schedules_list'),
    path('schedules/<int:pk>/', ScheduleDetailAPIView.as_view(), name='schedule_detail'),
    path('schedules/conflicts/', ConflictReportAPIView.as_view(), name='conflicts'),
]

