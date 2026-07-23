from django.urls import path
from backend.apps.analytics.api.views import (
    DashboardAPIView, KPIAPIView, ReportDefinitionAPIView
)

app_name = 'analytics_api'

urlpatterns = [
    path('dashboards/', DashboardAPIView.as_view(), name='dashboards'),
    path('kpis/', KPIAPIView.as_view(), name='kpis'),
    path('reports/', ReportDefinitionAPIView.as_view(), name='reports'),
]
