from django.urls import path
from backend.apps.academic.api.views import (
    AcademicSettingsAPIView, AcademicYearAPIView, EducationLevelAPIView, SubjectAPIView,
    TimetableCreateAPIView, TimetableScheduleAPIView, TimetablePublishAPIView,
    AttendanceCheckInAPIView, AttendanceSummaryAPIView,
    AssessmentCalculateAPIView, StudentResultReportAPIView,
    PromotionRunAPIView, GraduationRunAPIView, TranscriptDetailAPIView
)

app_name = 'academic_api'

urlpatterns = [
    path('academic/settings/', AcademicSettingsAPIView.as_view(), name='settings'),
    path('academic/years/', AcademicYearAPIView.as_view(), name='years'),
    path('academic/levels/', EducationLevelAPIView.as_view(), name='levels'),
    path('academic/subjects/', SubjectAPIView.as_view(), name='subjects'),
    path('academic/timetables/create/', TimetableCreateAPIView.as_view(), name='timetable_create'),
    path('academic/timetables/schedule/', TimetableScheduleAPIView.as_view(), name='timetable_schedule'),
    path('academic/timetables/publish/', TimetablePublishAPIView.as_view(), name='timetable_publish'),
    path('attendance/check-in/', AttendanceCheckInAPIView.as_view(), name='attendance_checkin'),
    path('attendance/student/', AttendanceSummaryAPIView.as_view(), name='attendance_summary'),
    path('assessment/calculate/', AssessmentCalculateAPIView.as_view(), name='assessment_calculate'),
    path('results/student/', StudentResultReportAPIView.as_view(), name='student_results'),
    path('promotion/run/', PromotionRunAPIView.as_view(), name='promotion_run'),
    path('graduation/run/', GraduationRunAPIView.as_view(), name='graduation_run'),
    path('transcript/<uuid:student_uuid>/', TranscriptDetailAPIView.as_view(), name='transcript_detail'),
]
