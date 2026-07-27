from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from backend.apps.inventory.models import (
    Supplier, PurchaseOrder, Warehouse, InventoryItem, StockMovement
)
from backend.apps.efbm.services.accounting import JournalPostingService
from backend.apps.core.services.notifications import UnifiedNotificationService

class ProcurementService:
    """
    Procurement & Purchasing Order Management Engine.
    """
    @classmethod
    @transaction.atomic
    def create_purchase_order(cls, school, supplier, item, quantity, unit_price):
        tenant = school.tenant
        total_amount = Decimal(str(quantity)) * Decimal(str(unit_price))

        po = PurchaseOrder.objects.create(
            tenant=tenant,
            supplier=supplier,
            order_date=timezone.now().date(),
            status='issued'
        )

        # Notify Supplier / Procurement Officer
        UnifiedNotificationService.send_notification(
            recipient="Procurement Officer",
            title="Purchase Order Issued",
            message=f"PO #{po.id} issued to {supplier.name} for {quantity}x {item.name} (${total_amount}).",
            channels=['in_app', 'email']
        )

        return {
            "status": "success",
            "po_id": str(po.id),
            "supplier": supplier.name,
            "item": item.name,
            "quantity": quantity,
            "total_amount": float(total_amount)
        }


class InventoryService:
    """
    Inventory Control Engine with Automatic Double-Entry General Ledger Integration.
    """
    @classmethod
    @transaction.atomic
    def receive_stock(cls, school, warehouse, item, quantity, unit_cost):
        tenant = school.tenant
        qty = int(quantity)
        total_val = Decimal(str(qty)) * Decimal(str(unit_cost))

        # 1. Update stock
        item.current_quantity += qty
        item.save()

        # 2. Record Stock Movement
        movement = StockMovement.objects.create(
            tenant=tenant,
            item=item,
            warehouse=warehouse,
            quantity_changed=qty,
            movement_type='receive',
            timestamp=timezone.now()
        )

        # 3. GL Accounting Integration (Debit Inventory Asset, Credit Accounts Payable)
        JournalPostingService.post_journal_entry(
            school=school,
            event_type="inventory_receipt",
            debit_account="Inventory Asset",
            credit_account="Accounts Payable (Suppliers)",
            amount=total_val
        )

        return {
            "status": "success",
            "sku": item.sku,
            "item_name": item.name,
            "quantity_received": qty,
            "new_total_quantity": item.current_quantity,
            "total_value": float(total_val),
            "movement_id": str(movement.id)
        }

    @classmethod
    @transaction.atomic
    def issue_stock(cls, school, warehouse, item, quantity, unit_cost=10.00):
        tenant = school.tenant
        qty = int(quantity)

        if item.current_quantity < qty:
            return {
                "status": "error",
                "message": f"Insufficient stock for {item.sku}. Available: {item.current_quantity}, Requested: {qty}"
            }

        total_val = Decimal(str(qty)) * Decimal(str(unit_cost))

        # 1. Update stock
        item.current_quantity -= qty
        item.save()

        # 2. Record Stock Movement
        movement = StockMovement.objects.create(
            tenant=tenant,
            item=item,
            warehouse=warehouse,
            quantity_changed=-qty,
            movement_type='consume',
            timestamp=timezone.now()
        )

        # 3. GL Accounting Integration (Debit Department Expense, Credit Inventory Asset)
        JournalPostingService.post_journal_entry(
            school=school,
            event_type="inventory_consumption",
            debit_account="Operating Supplies Expense",
            credit_account="Inventory Asset",
            amount=total_val
        )

        return {
            "status": "success",
            "sku": item.sku,
            "item_name": item.name,
            "quantity_issued": qty,
            "remaining_quantity": item.current_quantity,
            "total_value": float(total_val),
            "movement_id": str(movement.id)
        }
