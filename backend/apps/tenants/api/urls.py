from django.urls import path
from backend.apps.tenants.api.views import OnboardAPIView, CampusAPIView, DomainVerificationAPIView

app_name = 'tenants_api'

urlpatterns = [
    path('tenants/onboard/', OnboardAPIView.as_view(), name='onboard'),
    path('tenants/campuses/', CampusAPIView.as_view(), name='campuses_list'),
    path('tenants/domains/<uuid:pk>/verify/', DomainVerificationAPIView.as_view(), name='domain_verify'),
]
