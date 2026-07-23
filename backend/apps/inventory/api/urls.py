from django.urls import path
from backend.apps.inventory.api.views import (
    InventoryItemAPIView, WarehouseAPIView, PurchaseOrderAPIView
)

app_name = 'inventory_api'

urlpatterns = [
    path('items/', InventoryItemAPIView.as_view(), name='items'),
    path('warehouses/', WarehouseAPIView.as_view(), name='warehouses'),
    path('orders/', PurchaseOrderAPIView.as_view(), name='orders'),
]
