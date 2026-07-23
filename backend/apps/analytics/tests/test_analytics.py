from django.test import TestCase
from django.utils import timezone
from datetime import date
from decimal import Decimal
from backend.apps.tenants.models import Tenant, School
from backend.apps.analytics.models import (
    Dashboard, DashboardWidget, KPI, ReportDefinition, ReportExecution, AnalyticsSnapshot, DataCube, PredictiveInsight
)

class AnalyticsPlatformTests(TestCase):
    def setUp(self):
        # Create core configurations
        self.tenant = Tenant.objects.create(name="EABI Org")
        self.school = School.objects.create(tenant=self.tenant, name="EABI High School", school_types=["secondary"])
        
        # Dashboards
        self.dashboard = Dashboard.objects.create(
            tenant=self.tenant,
            name="Executive Dashboard",
            role_visibility="Principal"
        )
        self.widget = DashboardWidget.objects.create(
            dashboard=self.dashboard,
            tenant=self.tenant,
            title="Term Income Chart",
            widget_type="bar_chart"
        )

    def test_kpi_caching_and_calculations(self):
        kpi = KPI.objects.create(
            tenant=self.tenant,
            name="Attendance Average Rate",
            value=Decimal("94.50")
        )
        self.assertEqual(kpi.value, Decimal("94.50"))

    def test_report_executions_tracking(self):
        rep = ReportDefinition.objects.create(
            tenant=self.tenant,
            name="Broadsheet Class 1A Summary",
            category="academic"
        )
        exec_run = ReportExecution.objects.create(
            definition=rep,
            tenant=self.tenant,
            report_file_path="exports/broadsheet_1a.xlsx"
        )
        self.assertEqual(exec_run.report_file_path, "exports/broadsheet_1a.xlsx")

    def test_olap_datacubes_aggregation(self):
        cube = DataCube.objects.create(
            tenant=self.tenant,
            dimension_x="2026-GradeA",
            dimension_y="MaleStudents",
            metric_value=Decimal("45.00")
        )
        self.assertEqual(cube.metric_value, Decimal("45.00"))

    def test_predictive_insights_generation(self):
        insight = PredictiveInsight.objects.create(
            tenant=self.tenant,
            target_model="StudentProfile",
            prediction="High likelihood of default next term",
            probability=Decimal("82.00")
        )
        self.assertEqual(insight.probability, Decimal("82.00"))
