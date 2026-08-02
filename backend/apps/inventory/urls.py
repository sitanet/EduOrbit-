from django.urls import path, include
from django.views.generic import RedirectView
from backend.apps.inventory.views_web import (
    InventoryDashboardWebView, StockItemsWebView,
    FixedAssetRegisterWebView, DepreciationReportWebView
)

urlpatterns = [
    # Root redirect to dashboard
    path('', RedirectView.as_view(url='dashboard/', permanent=False)),
    # Web views
    path('dashboard/', InventoryDashboardWebView.as_view(), name='inventory_dashboard_web'),
    path('items/', StockItemsWebView.as_view(), name='stock_items_web'),
    path('assets/', FixedAssetRegisterWebView.as_view(), name='fixed_assets_web'),
    path('assets/depreciation/', DepreciationReportWebView.as_view(), name='depreciation_report_web'),
    
    # API endpoints versions
    path('api/v1/', include('backend.apps.inventory.api.urls')),
]
