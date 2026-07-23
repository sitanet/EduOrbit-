from django.urls import path
from backend.apps.eae.api.views import (
    QuestionAPIView, AssessmentAPIView, AttemptAPIView, AutoMarkAPIView
)

app_name = 'eae_api'

urlpatterns = [
    path('questions/', QuestionAPIView.as_view(), name='questions'),
    path('assessments/', AssessmentAPIView.as_view(), name='assessments'),
    path('attempts/', AttemptAPIView.as_view(), name='attempts'),
    path('attempts/<uuid:attempt_id>/automark/', AutoMarkAPIView.as_view(), name='automark'),
]
