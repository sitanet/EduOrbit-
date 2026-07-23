from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from backend.apps.inventory.models import InventoryItem, Warehouse, PurchaseOrder
from backend.apps.inventory.api.serializers import (
    ItemSerializer, WarehouseSerializer, OrderSerializer
)
from backend.apps.core.events import event_bus, DomainEvent

class InventoryItemAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        items = InventoryItem.objects.filter(tenant=request.tenant)
        serializer = ItemSerializer(items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = ItemSerializer(data=request.data)
        if serializer.is_valid():
            item = serializer.save(tenant=request.tenant)
            event_bus.publish(DomainEvent("inventory.item_created", tenant_id=str(request.tenant.id), data={"id": str(item.id)}))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WarehouseAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        warehouses = Warehouse.objects.filter(tenant=request.tenant)
        serializer = WarehouseSerializer(warehouses, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = WarehouseSerializer(data=request.data)
        if serializer.is_valid():
            wh = serializer.save(tenant=request.tenant)
            event_bus.publish(DomainEvent("warehouse.created", tenant_id=str(request.tenant.id), data={"id": str(wh.id)}))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PurchaseOrderAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        orders = PurchaseOrder.objects.filter(tenant=request.tenant)
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = OrderSerializer(data=request.data)
        if serializer.is_valid():
            po = serializer.save(tenant=request.tenant)
            event_bus.publish(DomainEvent("procurement.po_issued", tenant_id=str(request.tenant.id), data={"id": str(po.id)}))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
