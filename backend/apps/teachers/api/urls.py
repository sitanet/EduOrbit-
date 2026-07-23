from django.urls import path
from backend.apps.teachers.api.views import (
    CurriculumAPIView, LessonPlanAPIView, AssignmentAPIView, ObservationAPIView
)

app_name = 'teachers_api'

urlpatterns = [
    path('curricula/', CurriculumAPIView.as_view(), name='curricula'),
    path('lesson-plans/', LessonPlanAPIView.as_view(), name='lesson_plans'),
    path('assignments/', AssignmentAPIView.as_view(), name='assignments'),
    path('observations/', ObservationAPIView.as_view(), name='observations'),
]
