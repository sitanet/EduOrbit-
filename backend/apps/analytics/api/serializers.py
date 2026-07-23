from rest_framework import serializers
from backend.apps.analytics.models import (
    Dashboard, DashboardWidget, KPI, ReportDefinition, ReportExecution, AnalyticsSnapshot, DataCube, PredictiveInsight
)

class DashboardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dashboard
        fields = ['id', 'name', 'role_visibility']


class WidgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = DashboardWidget
        fields = ['id', 'dashboard', 'title', 'widget_type']


class KPISerializer(serializers.ModelSerializer):
    class Meta:
        model = KPI
        fields = ['id', 'name', 'value', 'last_calculated']


class ReportDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportDefinition
        fields = ['id', 'name', 'category']


class ReportExecutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportExecution
        fields = ['id', 'definition', 'executed_at', 'report_file_path']


class SnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalyticsSnapshot
        fields = ['id', 'metric_name', 'value', 'snapshot_date']


class DataCubeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataCube
        fields = ['id', 'dimension_x', 'dimension_y', 'metric_value']


class InsightSerializer(serializers.ModelSerializer):
    class Meta:
        model = PredictiveInsight
        fields = ['id', 'target_model', 'prediction', 'probability']
