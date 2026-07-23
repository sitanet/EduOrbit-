from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from backend.apps.tenants.models import Tenant, School
from backend.apps.people.models import Person
from backend.apps.inventory.models import (
    Supplier, PurchaseRequest, PurchaseOrder, Warehouse, InventoryItem, StockMovement, AssetCategory, Asset, AssetDepreciation
)

class InventoryPlatformTests(TestCase):
    def setUp(self):
        # Create core configurations
        self.tenant = Tenant.objects.create(name="EIPAM Org")
        self.school = School.objects.create(tenant=self.tenant, name="EIPAM Warehouse School", school_types=["secondary"])
        
        # Staff Person profile
        self.staff_person = Person.objects.create(
            tenant=self.tenant,
            person_number="P-101001",
            first_name="Winston",
            last_name="Smith",
            gender="male",
            date_of_birth="1984-04-04"
        )
        
        # Supplier
        self.supplier = Supplier.objects.create(
            tenant=self.tenant,
            name="Ministry of Plenty Stores",
            tin="TIN-8400",
            payment_terms="Net 30"
        )
        
        # Warehouse
        self.warehouse = Warehouse.objects.create(
            school=self.school,
            tenant=self.tenant,
            name="Main Bookstore Warehouse"
        )
        
        # Items
        self.item = InventoryItem.objects.create(
            sku="SKU-BOOK-01",
            name="1984 George Orwell Edition",
            tenant=self.tenant,
            current_quantity=100,
            reorder_level=20
        )
        
        # Asset
        self.category = AssetCategory.objects.create(tenant=self.tenant, name="Electronics")
        self.asset = Asset.objects.create(
            category=self.category,
            tenant=self.tenant,
            asset_number="AST-TELE-99",
            name="Telescreen 4K Monitor",
            purchase_cost=Decimal("1200.00"),
            current_value=Decimal("1200.00"),
            useful_life_years=5
        )

    def test_purchase_order_lifecycle(self):
        po = PurchaseOrder.objects.create(
            supplier=self.supplier,
            tenant=self.tenant,
            status="draft"
        )
        self.assertEqual(po.status, "draft")
        po.status = "issued"
        po.save()
        self.assertEqual(po.status, "issued")

    def test_stock_movement_deductions(self):
        # Adjust stock
        self.item.current_quantity -= 10
        self.item.save()
        
        move = StockMovement.objects.create(
            item=self.item,
            warehouse=self.warehouse,
            tenant=self.tenant,
            quantity_changed=-10,
            movement_type="consume"
        )
        self.assertEqual(self.item.current_quantity, 90)
        self.assertEqual(move.quantity_changed, -10)

    def test_asset_depreciation_runs(self):
        depr_amount = Decimal("240.00") # 1200 / 5 years
        self.asset.current_value -= depr_amount
        self.asset.save()
        
        run = AssetDepreciation.objects.create(
            asset=self.asset,
            tenant=self.tenant,
            depreciation_amount=depr_amount
        )
        self.assertEqual(self.asset.current_value, Decimal("960.00"))
        self.assertEqual(run.depreciation_amount, Decimal("240.00"))
