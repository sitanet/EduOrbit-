from rest_framework import serializers
from backend.apps.inventory.models import (
    Supplier, PurchaseRequest, PurchaseOrder, Warehouse, InventoryItem, InventoryBatch, StockMovement, AssetCategory, Asset, AssetDepreciation, AssetMaintenance
)

class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ['id', 'name', 'tin', 'payment_terms']


class RequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseRequest
        fields = ['id', 'requester', 'description', 'status']


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseOrder
        fields = ['id', 'supplier', 'order_date', 'status']


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = ['id', 'school', 'name']


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryItem
        fields = ['id', 'sku', 'name', 'current_quantity', 'reorder_level']


class BatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryBatch
        fields = ['id', 'item', 'batch_number', 'expiry_date', 'quantity']


class MovementSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockMovement
        fields = ['id', 'item', 'warehouse', 'quantity_changed', 'movement_type', 'timestamp']


class AssetCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetCategory
        fields = ['id', 'name']


class AssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = ['id', 'category', 'asset_number', 'name', 'purchase_cost', 'current_value', 'useful_life_years']


class DepreciationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetDepreciation
        fields = ['id', 'asset', 'calculation_date', 'depreciation_amount']
