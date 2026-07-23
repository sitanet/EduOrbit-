from django.urls import path
from backend.apps.administration.api.views import (
    PlatformSettingAPIView, ModuleLicenseAPIView, APIKeyAPIView
)

app_name = 'administration_api'

urlpatterns = [
    path('settings/', PlatformSettingAPIView.as_view(), name='settings'),
    path('licenses/', ModuleLicenseAPIView.as_view(), name='licenses'),
    path('apikeys/', APIKeyAPIView.as_view(), name='apikeys'),
]
