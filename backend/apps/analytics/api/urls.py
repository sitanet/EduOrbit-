from django.urls import path
from backend.apps.analytics.api.views import (
    DashboardListAPIView, DashboardWidgetCreateAPIView, KPIListAPIView, TrendsAPIView, BenchmarksAPIView,
    ReportListAPIView, ReportExportAPIView, ReportScheduleAPIView, ExecutiveSummaryAPIView
)

app_name = 'analytics_api'

urlpatterns = [
    path('dashboard/', DashboardListAPIView.as_view(), name='dashboard_list'),
    path('dashboard/widgets/', DashboardWidgetCreateAPIView.as_view(), name='dashboard_widget_create'),
    path('kpis/', KPIListAPIView.as_view(), name='kpi_list'),
    path('trends/', TrendsAPIView.as_view(), name='trends_list'),
    path('benchmarks/', BenchmarksAPIView.as_view(), name='benchmarks_list'),
    path('reports/', ReportListAPIView.as_view(), name='report_list'),
    path('reports/export/', ReportExportAPIView.as_view(), name='report_export'),
    path('reports/schedule/', ReportScheduleAPIView.as_view(), name='report_schedule'),
    path('executive-summary/', ExecutiveSummaryAPIView.as_view(), name='executive_summary'),
]
