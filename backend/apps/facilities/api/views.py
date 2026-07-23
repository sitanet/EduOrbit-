from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from backend.apps.facilities.models import Building, Room, WorkOrder
from backend.apps.facilities.api.serializers import (
    BuildingSerializer, RoomSerializer, OrderSerializer
)
from backend.apps.core.events import event_bus, DomainEvent

class BuildingAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        buildings = Building.objects.filter(tenant=request.tenant)
        serializer = BuildingSerializer(buildings, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = BuildingSerializer(data=request.data)
        if serializer.is_valid():
            bld = serializer.save(tenant=request.tenant)
            event_bus.publish(DomainEvent("building.created", tenant_id=str(request.tenant.id), data={"id": str(bld.id)}))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RoomAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        rooms = Room.objects.filter(tenant=request.tenant)
        serializer = RoomSerializer(rooms, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = RoomSerializer(data=request.data)
        if serializer.is_valid():
            rm = serializer.save(tenant=request.tenant)
            event_bus.publish(DomainEvent("room.created", tenant_id=str(request.tenant.id), data={"id": str(rm.id)}))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WorkOrderAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        orders = WorkOrder.objects.filter(tenant=request.tenant)
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = OrderSerializer(data=request.data)
        if serializer.is_valid():
            wo = serializer.save(tenant=request.tenant)
            event_bus.publish(DomainEvent("workorder.assigned", tenant_id=str(request.tenant.id), data={"id": str(wo.id)}))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
