from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from backend.apps.tenants.models import School
from backend.apps.analytics.models import Dashboard, KPI, ReportDefinition
from backend.apps.analytics.services.bi import (
    KPIService, ExecutiveInsightService, ReportService, WidgetService, TrendAnalysisService, BenchmarkService, ScheduledReportService
)

class DashboardWidgetCreateAPIView(APIView):
    def post(self, request):
        dashboard_id = request.data.get('dashboard_id')
        title = request.data.get('title')
        widget_type = request.data.get('widget_type', 'bar_chart')

        try:
            dashboard = Dashboard.objects.get(id=dashboard_id)
            res = WidgetService.configure_widget(dashboard=dashboard, title=title, widget_type=widget_type)
            return Response({"status": "success", "data": res}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class TrendsAPIView(APIView):
    def get(self, request):
        school_id = request.query_params.get('school_id')
        try:
            school = School.objects.get(id=school_id)
            res = TrendAnalysisService.get_growth_trends(school=school)
            return Response({"status": "success", "data": res}, status=status.HTTP_200_OK)
        except School.DoesNotExist:
            return Response({"status": "error", "message": "School not found."}, status=status.HTTP_404_NOT_FOUND)


class BenchmarksAPIView(APIView):
    def get(self, request):
        school_id = request.query_params.get('school_id')
        try:
            school = School.objects.get(id=school_id)
            res = BenchmarkService.get_school_benchmarks(school=school)
            return Response({"status": "success", "data": res}, status=status.HTTP_200_OK)
        except School.DoesNotExist:
            return Response({"status": "error", "message": "School not found."}, status=status.HTTP_404_NOT_FOUND)


class ReportScheduleAPIView(APIView):
    def post(self, request):
        school_id = request.data.get('school_id')
        report_name = request.data.get('report_name', 'Monthly Executive Report')
        frequency = request.data.get('frequency', 'monthly')

        try:
            school = School.objects.get(id=school_id)
            res = ScheduledReportService.schedule_report(school=school, report_name=report_name, frequency=frequency)
            return Response({"status": "success", "data": res}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class DashboardListAPIView(APIView):
    def get(self, request):
        dashboards = Dashboard.objects.all()
        data = [
            {
                "id": str(d.id),
                "name": d.name,
                "role_visibility": d.role_visibility,
                "widgets_count": d.widgets.count()
            }
            for d in dashboards
        ]
        return Response({"status": "success", "count": len(data), "data": data})


class KPIListAPIView(APIView):
    def get(self, request):
        kpis = KPI.objects.all()
        data = [
            {
                "id": str(k.id),
                "name": k.name,
                "value": float(k.value),
                "last_calculated": str(k.last_calculated)
            }
            for k in kpis
        ]
        return Response({"status": "success", "count": len(data), "data": data})


class ReportListAPIView(APIView):
    def get(self, request):
        reports = ReportDefinition.objects.all()
        data = [
            {
                "id": str(r.id),
                "name": r.name,
                "category": r.category
            }
            for r in reports
        ]
        return Response({"status": "success", "count": len(data), "data": data})


class ReportExportAPIView(APIView):
    def post(self, request):
        school_id = request.data.get('school_id')
        report_name = request.data.get('report_name', 'Executive Master Report')
        file_format = request.data.get('file_format', 'pdf')

        try:
            school = School.objects.get(id=school_id)
            res = ReportService.generate_report(school=school, report_name=report_name, file_format=file_format)
            return Response({"status": "success", "data": res}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ExecutiveSummaryAPIView(APIView):
    def get(self, request):
        school_id = request.query_params.get('school_id')
        try:
            school = School.objects.get(id=school_id)
            res = ExecutiveInsightService.generate_school_summary(school=school)
            return Response({"status": "success", "data": res}, status=status.HTTP_200_OK)
        except School.DoesNotExist:
            return Response({"status": "error", "message": "School not found."}, status=status.HTTP_404_NOT_FOUND)
