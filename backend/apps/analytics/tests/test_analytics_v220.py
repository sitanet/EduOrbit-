from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from backend.apps.tenants.models import Tenant, School
from backend.apps.analytics.models import Dashboard, DashboardWidget, KPI, ReportDefinition
from backend.apps.analytics.services.bi import (
    DashboardService, KPIService, AnalyticsService, ExecutiveInsightService, ReportService,
    WidgetService, TrendAnalysisService, BenchmarkService, ScheduledReportService, ExportService
)

class AnalyticsV220TestCase(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Analytics Tenant")
        self.school = School.objects.create(tenant=self.tenant, name="Imperial College of Technology")
        self.dashboard = Dashboard.objects.create(tenant=self.tenant, name="Principal Executive Board", role_visibility="Principal")
        self.widget = DashboardWidget.objects.create(tenant=self.tenant, dashboard=self.dashboard, title="Revenue vs Expenses", widget_type="bar_chart")
        self.report_def = ReportDefinition.objects.create(tenant=self.tenant, name="Q4 Performance Report", category="executive")
        self.client = APIClient()

    def test_analytics_and_bi_services(self):
        # 1. Dashboard & Widget Services
        dash_res = DashboardService.create_dashboard(tenant=self.tenant, name="Finance Director Board", role_visibility="Accountant")
        self.assertEqual(dash_res["status"], "success")

        wgt_res = WidgetService.configure_widget(dashboard=self.dashboard, title="Student Growth", widget_type="line_chart")
        self.assertEqual(wgt_res["status"], "success")

        # 2. KPI Calculation & Trends
        kpi_res = KPIService.calculate_kpis(school=self.school)
        self.assertEqual(kpi_res["status"], "success")

        trd_res = TrendAnalysisService.get_growth_trends(school=self.school)
        self.assertEqual(trd_res["status"], "success")

        bmk_res = BenchmarkService.get_school_benchmarks(school=self.school)
        self.assertEqual(bmk_res["status"], "success")

        # 3. Report Generation, Scheduling & Export
        sch_res = ScheduledReportService.schedule_report(school=self.school, report_name="Monthly Financial Audit", frequency="monthly")
        self.assertEqual(sch_res["status"], "success")

        exp_res = ExportService.export_dataset(dataset_name="Student Attendance Dataset", file_format="csv")
        self.assertEqual(exp_res["status"], "success")

    def test_analytics_api_endpoints(self):
        # 1. Dashboard List API
        d_url = '/analytics/api/v1/dashboard/'
        resp = self.client.get(d_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # 2. Trends API
        t_url = f'/analytics/api/v1/trends/?school_id={self.school.id}'
        t_resp = self.client.get(t_url)
        self.assertEqual(t_resp.status_code, status.HTTP_200_OK)

        # 3. Benchmarks API
        b_url = f'/analytics/api/v1/benchmarks/?school_id={self.school.id}'
        b_resp = self.client.get(b_url)
        self.assertEqual(b_resp.status_code, status.HTTP_200_OK)

        # 4. Report Schedule API
        sch_url = '/analytics/api/v1/reports/schedule/'
        payload = {
            "school_id": str(self.school.id),
            "report_name": "Executive Master Report",
            "frequency": "monthly"
        }
        sch_resp = self.client.post(sch_url, payload, format='json')
        self.assertEqual(sch_resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(sch_resp.data["status"], "success")
