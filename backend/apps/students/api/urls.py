from django.urls import path
from backend.apps.students.api.views import (
    StudentListAPIView, StudentEnrollmentAPIView, PromoteStudentAPIView, WithdrawStudentAPIView, StudentRecordAPIView, StudentTransitionAPIView
)

app_name = 'students_api'

urlpatterns = [
    path('students/', StudentListAPIView.as_view(), name='student_list'),
    path('enroll/', StudentEnrollmentAPIView.as_view(), name='student_enroll'),
    path('students/enroll/', StudentEnrollmentAPIView.as_view(), name='student_enroll_legacy'),
    path('students/<uuid:pk>/transition/', StudentTransitionAPIView.as_view(), name='student_transition_api'),
    path('promote/', PromoteStudentAPIView.as_view(), name='student_promote'),
    path('withdraw/', WithdrawStudentAPIView.as_view(), name='student_withdraw'),
    path('student-record/', StudentRecordAPIView.as_view(), name='student_record'),
]
