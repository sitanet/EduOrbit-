from django.urls import path
from backend.apps.eae.api.views import (
    QuestionBankListAPIView, ExamListAPIView, ExamStartAPIView, ExamSubmitAPIView,
    ResultListAPIView, ResultPublishAPIView
)

app_name = 'cbt_api'

urlpatterns = [
    path('question-banks/', QuestionBankListAPIView.as_view(), name='question_banks'),
    path('exams/', ExamListAPIView.as_view(), name='exam_list'),
    path('start/', ExamStartAPIView.as_view(), name='exam_start'),
    path('submit/', ExamSubmitAPIView.as_view(), name='exam_submit'),
    path('results/', ResultListAPIView.as_view(), name='result_list'),
    path('results/publish/', ResultPublishAPIView.as_view(), name='result_publish'),
]
