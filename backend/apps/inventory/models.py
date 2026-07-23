import uuid
from django.db import models
from django.utils import timezone
from backend.apps.core.models import TenantBaseModel, PlatformBaseModel

# ==============================================================
# PROCUREMENT ENGINE
# ==============================================================

class Supplier(TenantBaseModel):
    name = models.CharField(max_length=150)
    tin = models.CharField(max_length=50, blank=True)
    payment_terms = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.name


class PurchaseRequest(TenantBaseModel):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ]
    requester = models.ForeignKey('people.Person', on_delete=models.CASCADE, related_name='purchase_requests')
    description = models.TextField()
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='draft')

    def __str__(self):
        return f"Req: {self.description[:30]} ({self.status})"


class PurchaseOrder(TenantBaseModel):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('issued', 'Issued'),
        ('received', 'Received'),
        ('cancelled', 'Cancelled')
    ]
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='orders')
    order_date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='draft')

    def __str__(self):
        return f"PO: {self.id} for {self.supplier.name} ({self.status})"


# ==============================================================
# WAREHOUSE MANAGEMENT
# ==============================================================

class Warehouse(TenantBaseModel):
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class InventoryItem(TenantBaseModel):
    sku = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=150)
    current_quantity = models.IntegerField(default=0)
    reorder_level = models.IntegerField(default=10)

    def __str__(self):
        return f"{self.name} ({self.sku})"


class InventoryBatch(TenantBaseModel):
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='batches')
    batch_number = models.CharField(max_length=100)
    expiry_date = models.DateField(null=True, blank=True)
    quantity = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.item.name} Batch {self.batch_number}"


class StockMovement(TenantBaseModel):
    """
    Audit log auditing stock adjustments, transfers, and disposals.
    """
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='movements')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='movements')
    quantity_changed = models.IntegerField()
    movement_type = models.CharField(max_length=30)  # receive, transfer, adjust, consume
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.movement_type}: {self.quantity_changed} of {self.item.sku}"


# ==============================================================
# ASSET MANAGEMENT
# ==============================================================

class AssetCategory(TenantBaseModel):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Asset(TenantBaseModel):
    category = models.ForeignKey(AssetCategory, on_delete=models.CASCADE, related_name='assets')
    asset_number = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=150)
    purchase_cost = models.DecimalField(max_digits=12, decimal_places=2)
    current_value = models.DecimalField(max_digits=12, decimal_places=2)
    useful_life_years = models.IntegerField(default=5)

    def __str__(self):
        return f"{self.asset_number}: {self.name}"


class AssetDepreciation(TenantBaseModel):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='depreciations')
    calculation_date = models.DateField(default=timezone.now)
    depreciation_amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Depr: {self.asset.asset_number} amount {self.depreciation_amount}"


class AssetMaintenance(TenantBaseModel):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='maintenance_records')
    description = models.CharField(max_length=200)
    maintenance_date = models.DateField()

    def __str__(self):
        return f"Maint for {self.asset.asset_number} on {self.maintenance_date}"
