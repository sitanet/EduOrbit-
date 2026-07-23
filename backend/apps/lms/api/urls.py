from django.urls import path
from backend.apps.lms.api.views import (
    ModuleAPIView, UnitAPIView, ProgressAPIView
)

app_name = 'lms_api'

urlpatterns = [
    path('modules/', ModuleAPIView.as_view(), name='modules'),
    path('units/', UnitAPIView.as_view(), name='units'),
    path('progress/', ProgressAPIView.as_view(), name='progress'),
]
