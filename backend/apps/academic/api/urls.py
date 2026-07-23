from django.urls import path
from backend.apps.academic.api.views import (
    AcademicSettingsAPIView, AcademicYearAPIView, EducationLevelAPIView, SubjectAPIView
)

app_name = 'academic_api'

urlpatterns = [
    path('academic/settings/', AcademicSettingsAPIView.as_view(), name='settings'),
    path('academic/years/', AcademicYearAPIView.as_view(), name='years'),
    path('academic/levels/', EducationLevelAPIView.as_view(), name='levels'),
    path('academic/subjects/', SubjectAPIView.as_view(), name='subjects'),
]
