from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from backend.apps.analytics.models import Dashboard, KPI, ReportDefinition
from backend.apps.analytics.api.serializers import (
    DashboardSerializer, KPISerializer, ReportDefinitionSerializer
)
from backend.apps.core.events import event_bus, DomainEvent

class DashboardAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        dashboards = Dashboard.objects.filter(tenant=request.tenant)
        serializer = DashboardSerializer(dashboards, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = DashboardSerializer(data=request.data)
        if serializer.is_valid():
            dash = serializer.save(tenant=request.tenant)
            event_bus.publish(DomainEvent("analytics.dashboard_created", tenant_id=str(request.tenant.id), data={"id": str(dash.id)}))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class KPIAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        kpis = KPI.objects.filter(tenant=request.tenant)
        serializer = KPISerializer(kpis, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = KPISerializer(data=request.data)
        if serializer.is_valid():
            kpi = serializer.save(tenant=request.tenant)
            event_bus.publish(DomainEvent("analytics.kpi_updated", tenant_id=str(request.tenant.id), data={"id": str(kpi.id)}))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ReportDefinitionAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        defs = ReportDefinition.objects.filter(tenant=request.tenant)
        serializer = ReportDefinitionSerializer(defs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = ReportDefinitionSerializer(data=request.data)
        if serializer.is_valid():
            rep = serializer.save(tenant=request.tenant)
            event_bus.publish(DomainEvent("analytics.report_defined", tenant_id=str(request.tenant.id), data={"id": str(rep.id)}))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
