from django.urls import path
from backend.apps.lms.api.views import (
    CourseListAPIView, LessonListAPIView, QuizListAPIView, QuizSubmitAPIView, AssignmentSubmitAPIView
)

app_name = 'lms_api'

urlpatterns = [
    path('courses/', CourseListAPIView.as_view(), name='course_list'),
    path('lessons/', LessonListAPIView.as_view(), name='lesson_list'),
    path('quizzes/', QuizListAPIView.as_view(), name='quiz_list'),
    path('quizzes/submit/', QuizSubmitAPIView.as_view(), name='quiz_submit'),
    path('submissions/', AssignmentSubmitAPIView.as_view(), name='assignment_submit'),
]
