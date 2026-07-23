import uuid
from django.db import models
from django.utils import timezone
from backend.apps.core.models import TenantBaseModel, PlatformBaseModel

# ==============================================================
# DASHBOARD LAYOUTS & WIDGETS
# ==============================================================

class Dashboard(TenantBaseModel):
    name = models.CharField(max_length=150)
    role_visibility = models.CharField(max_length=100)  # Principal, Accountant

    def __str__(self):
        return self.name


class DashboardWidget(TenantBaseModel):
    dashboard = models.ForeignKey(Dashboard, on_delete=models.CASCADE, related_name='widgets')
    title = models.CharField(max_length=150)
    widget_type = models.CharField(max_length=50)  # bar_chart, line_chart, value_card

    def __str__(self):
        return f"{self.title} ({self.widget_type})"


# ==============================================================
# KEY PERFORMANCE INDICATORS & REPORTS
# ==============================================================

class KPI(TenantBaseModel):
    name = models.CharField(max_length=150)
    value = models.DecimalField(max_digits=12, decimal_places=2)
    last_calculated = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.name}: {self.value}"


class ReportDefinition(TenantBaseModel):
    name = models.CharField(max_length=150)
    category = models.CharField(max_length=100)  # finance, academic, student

    def __str__(self):
        return self.name


class ReportExecution(TenantBaseModel):
    definition = models.ForeignKey(ReportDefinition, on_delete=models.CASCADE, related_name='executions')
    executed_at = models.DateTimeField(default=timezone.now)
    report_file_path = models.CharField(max_length=255)  # Path to generated file

    def __str__(self):
        return f"{self.definition.name} run at {self.executed_at}"


# ==============================================================
# OLAP DATA CUBES & PREDICTIONS
# ==============================================================

class AnalyticsSnapshot(TenantBaseModel):
    metric_name = models.CharField(max_length=100)
    value = models.DecimalField(max_digits=12, decimal_places=2)
    snapshot_date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"{self.metric_name} on {self.snapshot_date}: {self.value}"


class DataCube(TenantBaseModel):
    """
    Multidimensional OLAP dataset slices.
    """
    dimension_x = models.CharField(max_length=100)
    dimension_y = models.CharField(max_length=100)
    metric_value = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"Cube: {self.dimension_x}/{self.dimension_y} = {self.metric_value}"


class PredictiveInsight(TenantBaseModel):
    """
    AI forecasts (dropout risks, default risks).
    """
    target_model = models.CharField(max_length=100)  # Student, Invoice
    prediction = models.TextField()
    probability = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Prediction: {self.target_model} (Prob: {self.probability})"
