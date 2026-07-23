from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from backend.apps.tenants.models import School
from backend.apps.inventory.models import Warehouse, InventoryItem, Asset


class InventoryDashboardWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        tenant = getattr(request, 'tenant', None)
        warehouses = Warehouse.objects.filter(tenant=tenant) if tenant else []
        assets = Asset.objects.filter(tenant=tenant).select_related('category') if tenant else []
        low_stock_items = []
        if tenant:
            try:
                low_stock_items = InventoryItem.objects.filter(tenant=tenant)
            except Exception:
                low_stock_items = []

        context = {
            'warehouses': warehouses,
            'assets': assets,
            'low_stock_items': low_stock_items,
        }
        return render(request, 'inventory/dashboard.html', context)


class StockItemsWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        tenant = getattr(request, 'tenant', None)
        items = InventoryItem.objects.filter(tenant=tenant) if tenant else []
        return render(request, 'inventory/items.html', {'items': items})
