from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from backend.apps.tenants.models import Tenant, School
from backend.apps.inventory.models import Supplier, Warehouse, InventoryItem
from backend.apps.inventory.services.procurement import ProcurementService, InventoryService

class ProcurementInventoryRelease3TestCase(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Procurement Tenant")
        self.school = School.objects.create(tenant=self.tenant, name="Saint Marks Science Academy")
        self.supplier = Supplier.objects.create(tenant=self.tenant, name="Global Lab Supplies Ltd")
        self.warehouse = Warehouse.objects.create(tenant=self.tenant, school=self.school, name="Central Science Store")
        self.item = InventoryItem.objects.create(
            tenant=self.tenant, sku="LAB-MIC-001", name="Digital Microscope", current_quantity=5, reorder_level=2
        )
        self.client = APIClient()

    def test_procurement_and_inventory_service_flow(self):
        # 1. Create Purchase Order
        po_res = ProcurementService.create_purchase_order(
            school=self.school, supplier=self.supplier, item=self.item, quantity=10, unit_price=150.00
        )
        self.assertEqual(po_res["status"], "success")

        # 2. Receive Stock (Updates inventory & posts GL Journal entry)
        rec_res = InventoryService.receive_stock(
            school=self.school, warehouse=self.warehouse, item=self.item, quantity=10, unit_cost=150.00
        )
        self.assertEqual(rec_res["status"], "success")
        self.item.refresh_from_db()
        self.assertEqual(self.item.current_quantity, 15)

        # 3. Issue Stock (Debits expense & posts GL Journal entry)
        iss_res = InventoryService.issue_stock(
            school=self.school, warehouse=self.warehouse, item=self.item, quantity=3, unit_cost=150.00
        )
        self.assertEqual(iss_res["status"], "success")
        self.item.refresh_from_db()
        self.assertEqual(self.item.current_quantity, 12)

    def test_inventory_api_endpoints(self):
        # 1. Receive Stock API
        rec_url = '/inventory/api/v1/stock/receive/'
        payload = {
            "school_id": str(self.school.id),
            "warehouse_id": str(self.warehouse.id),
            "item_id": str(self.item.id),
            "quantity": 5,
            "unit_cost": 200.00
        }
        resp = self.client.post(rec_url, payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["status"], "success")

        # 2. List Inventory Items API
        list_url = '/inventory/api/v1/items/'
        list_resp = self.client.get(list_url)
        self.assertEqual(list_resp.status_code, status.HTTP_200_OK)
        self.assertTrue(list_resp.data["count"] > 0)
