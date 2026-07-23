from django.urls import path
from backend.apps.admissions.api.views import (
    CampaignAPIView, IntakeAPIView, ApplicationAPIView, EnrollmentAPIView
)

app_name = 'admissions_api'

urlpatterns = [
    path('admissions/campaigns/', CampaignAPIView.as_view(), name='campaigns'),
    path('admissions/intakes/', IntakeAPIView.as_view(), name='intakes'),
    path('admissions/applications/', ApplicationAPIView.as_view(), name='applications'),
    path('admissions/enrollment/', EnrollmentAPIView.as_view(), name='enroll'),
]
