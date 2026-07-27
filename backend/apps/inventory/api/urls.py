from django.urls import path
from backend.apps.inventory.api.views import (
    PurchaseOrderCreateAPIView, StockReceiveAPIView, StockIssueAPIView, InventoryItemListAPIView,
    AssetRegisterAPIView, AssetDepreciationRunAPIView, AssetListAPIView
)

app_name = 'inventory_api'

urlpatterns = [
    path('purchase-order/', PurchaseOrderCreateAPIView.as_view(), name='purchase_order_create'),
    path('stock/receive/', StockReceiveAPIView.as_view(), name='stock_receive'),
    path('stock/issue/', StockIssueAPIView.as_view(), name='stock_issue'),
    path('items/', InventoryItemListAPIView.as_view(), name='inventory_items'),
    path('assets/register/', AssetRegisterAPIView.as_view(), name='asset_register'),
    path('assets/depreciation/run/', AssetDepreciationRunAPIView.as_view(), name='asset_depreciation_run'),
    path('assets/', AssetListAPIView.as_view(), name='asset_list'),
]
