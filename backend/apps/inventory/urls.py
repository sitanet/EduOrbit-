from django.urls import path, include
from backend.apps.inventory.views_web import InventoryDashboardWebView, StockItemsWebView

urlpatterns = [
    # Web views
    path('dashboard/', InventoryDashboardWebView.as_view(), name='inventory_dashboard_web'),
    path('items/', StockItemsWebView.as_view(), name='stock_items_web'),
    
    # API endpoints versions
    path('api/v1/', include('backend.apps.inventory.api.urls')),
]
