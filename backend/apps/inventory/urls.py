from django.urls import path, include
from django.views.generic import RedirectView
from backend.apps.inventory.views_web import InventoryDashboardWebView, StockItemsWebView

urlpatterns = [
    # Root redirect to dashboard
    path('', RedirectView.as_view(url='dashboard/', permanent=False)),
    # Web views
    path('dashboard/', InventoryDashboardWebView.as_view(), name='inventory_dashboard_web'),
    path('items/', StockItemsWebView.as_view(), name='stock_items_web'),
    
    # API endpoints versions
    path('api/v1/', include('backend.apps.inventory.api.urls')),
]
