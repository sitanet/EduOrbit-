from django.urls import path
from backend.apps.admissions.api.views import ApplicationListAPIView, ApplicantConversionAPIView

app_name = 'admissions_api'

urlpatterns = [
    path('applications/', ApplicationListAPIView.as_view(), name='application_list'),
    path('applications/convert/', ApplicantConversionAPIView.as_view(), name='applicant_convert'),
]
