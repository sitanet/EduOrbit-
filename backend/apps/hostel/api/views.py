from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from backend.apps.hostel.models import BedAllocation, HostelRollCall, HostelVisitor
from backend.apps.hostel.api.serializers import (
    AllocationSerializer, RollCallSerializer, VisitorSerializer
)
from backend.apps.core.events import event_bus, DomainEvent

class BedAllocationAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        allocations = BedAllocation.objects.filter(tenant=request.tenant)
        serializer = AllocationSerializer(allocations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = AllocationSerializer(data=request.data)
        if serializer.is_valid():
            alloc = serializer.save(tenant=request.tenant)
            event_bus.publish(DomainEvent("bed.allocated", tenant_id=str(request.tenant.id), data={"id": str(alloc.id)}))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class HostelRollCallAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        rollcalls = HostelRollCall.objects.filter(tenant=request.tenant)
        serializer = RollCallSerializer(rollcalls, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = RollCallSerializer(data=request.data)
        if serializer.is_valid():
            rc = serializer.save(tenant=request.tenant)
            event_bus.publish(DomainEvent("hostel.rollcall_logged", tenant_id=str(request.tenant.id), data={"id": str(rc.id)}))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class HostelVisitorAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        visitors = HostelVisitor.objects.filter(tenant=request.tenant)
        serializer = VisitorSerializer(visitors, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = VisitorSerializer(data=request.data)
        if serializer.is_valid():
            vis = serializer.save(tenant=request.tenant)
            event_bus.publish(DomainEvent("hostel.visitor_logged", tenant_id=str(request.tenant.id), data={"id": str(vis.id)}))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
