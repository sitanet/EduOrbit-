from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from backend.apps.tenants.models import School
from backend.apps.inventory.models import Supplier, Warehouse, InventoryItem, PurchaseOrder
from backend.apps.inventory.services.procurement import ProcurementService, InventoryService

class PurchaseOrderCreateAPIView(APIView):
    def post(self, request):
        school_id = request.data.get('school_id')
        supplier_id = request.data.get('supplier_id')
        item_id = request.data.get('item_id')
        quantity = request.data.get('quantity', 1)
        unit_price = request.data.get('unit_price', 0.00)

        try:
            school = School.objects.get(id=school_id)
            supplier = Supplier.objects.get(id=supplier_id)
            item = InventoryItem.objects.get(id=item_id)

            res = ProcurementService.create_purchase_order(
                school=school, supplier=supplier, item=item, quantity=quantity, unit_price=unit_price
            )
            return Response({"status": "success", "data": res}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class StockReceiveAPIView(APIView):
    def post(self, request):
        school_id = request.data.get('school_id')
        warehouse_id = request.data.get('warehouse_id')
        item_id = request.data.get('item_id')
        quantity = request.data.get('quantity', 1)
        unit_cost = request.data.get('unit_cost', 0.00)

        try:
            school = School.objects.get(id=school_id)
            warehouse = Warehouse.objects.get(id=warehouse_id)
            item = InventoryItem.objects.get(id=item_id)

            res = InventoryService.receive_stock(
                school=school, warehouse=warehouse, item=item, quantity=quantity, unit_cost=unit_cost
            )
            return Response({"status": "success", "data": res}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class StockIssueAPIView(APIView):
    def post(self, request):
        school_id = request.data.get('school_id')
        warehouse_id = request.data.get('warehouse_id')
        item_id = request.data.get('item_id')
        quantity = request.data.get('quantity', 1)
        unit_cost = request.data.get('unit_cost', 10.00)

        try:
            school = School.objects.get(id=school_id)
            warehouse = Warehouse.objects.get(id=warehouse_id)
            item = InventoryItem.objects.get(id=item_id)

            res = InventoryService.issue_stock(
                school=school, warehouse=warehouse, item=item, quantity=quantity, unit_cost=unit_cost
            )
            return Response({"status": "success" if res["status"] == "success" else "error", "data": res}, status=status.HTTP_200_OK if res["status"] == "success" else status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class InventoryItemListAPIView(APIView):
    def get(self, request):
        items = InventoryItem.objects.all()
        data = [
            {
                "id": str(i.id),
                "sku": i.sku,
                "name": i.name,
                "current_quantity": i.current_quantity,
                "reorder_level": i.reorder_level
            }
            for i in items
        ]
        return Response({"status": "success", "count": len(data), "data": data})


# ==============================================================
# ENTERPRISE FIXED ASSET MANAGEMENT (EAM) API VIEWS
# ==============================================================

from backend.apps.inventory.models import AssetCategory, Asset
from backend.apps.inventory.services.assets import AssetRegistrationService, DepreciationService

class AssetRegisterAPIView(APIView):
    def post(self, request):
        school_id = request.data.get('school_id')
        category_id = request.data.get('category_id')
        name = request.data.get('name')
        purchase_cost = request.data.get('purchase_cost', 0.00)
        useful_life_years = request.data.get('useful_life_years', 5)

        try:
            school = School.objects.get(id=school_id)
            category = AssetCategory.objects.get(id=category_id)
            res = AssetRegistrationService.register_asset(
                school=school, category=category, name=name, purchase_cost=purchase_cost, useful_life_years=useful_life_years
            )
            return Response({"status": "success", "data": res}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AssetDepreciationRunAPIView(APIView):
    def post(self, request):
        school_id = request.data.get('school_id')
        asset_id = request.data.get('asset_id')

        try:
            school = School.objects.get(id=school_id)
            asset = Asset.objects.get(id=asset_id)
            res = DepreciationService.run_monthly_depreciation(school=school, asset=asset)
            return Response({"status": "success", "data": res}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AssetListAPIView(APIView):
    def get(self, request):
        assets = Asset.objects.all()
        data = [
            {
                "id": str(a.id),
                "asset_number": a.asset_number,
                "name": a.name,
                "category": a.category.name,
                "purchase_cost": float(a.purchase_cost),
                "current_value": float(a.current_value)
            }
            for a in assets
        ]
        return Response({"status": "success", "count": len(data), "data": data})

