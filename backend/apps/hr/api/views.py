from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from backend.apps.hr.models import EmployeeProfile, LeaveRequest, PayrollRun
from backend.apps.hr.api.serializers import (
    EmployeeSerializer, LeaveRequestSerializer, PayrollRunSerializer
)
from backend.apps.core.events import event_bus, DomainEvent

class EmployeeProfileAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        employees = EmployeeProfile.objects.filter(tenant=request.tenant)
        serializer = EmployeeSerializer(employees, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = EmployeeSerializer(data=request.data)
        if serializer.is_valid():
            emp = serializer.save(tenant=request.tenant)
            event_bus.publish(DomainEvent("employee.hired", tenant_id=str(request.tenant.id), data={"id": str(emp.id)}))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LeaveRequestAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        leaves = LeaveRequest.objects.filter(tenant=request.tenant)
        serializer = LeaveRequestSerializer(leaves, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = LeaveRequestSerializer(data=request.data)
        if serializer.is_valid():
            leave = serializer.save(tenant=request.tenant)
            event_bus.publish(DomainEvent("leave.requested", tenant_id=str(request.tenant.id), data={"id": str(leave.id)}))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PayrollRunAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        payroll = PayrollRun.objects.filter(tenant=request.tenant)
        serializer = PayrollRunSerializer(payroll, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = PayrollRunSerializer(data=request.data)
        if serializer.is_valid():
            pay = serializer.save(tenant=request.tenant)
            event_bus.publish(DomainEvent("payroll.generated", tenant_id=str(request.tenant.id), data={"id": str(pay.id)}))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
