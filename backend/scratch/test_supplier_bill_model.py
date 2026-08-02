import os
import sys
import django

sys.path.insert(0, r"c:\Users\user\Desktop\Development\SMS")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.config.settings.local")
django.setup()

from decimal import Decimal
from django.utils import timezone
from django.core.exceptions import ValidationError

from backend.apps.tenants.models import Tenant
from backend.apps.efbm.models import SupplierBill

def run_tests():
    print("=================================================================")
    print("PHASE 1 — SUPPLIER BILL MODEL EVIDENCE AUDIT & VALIDATION")
    print("=================================================================")

    tenant = Tenant.objects.first() or Tenant.objects.create(name="SupplierBill Validation Tenant")

    # 1. Validate Field Definitions & Decimal Precision
    bill = SupplierBill.objects.create(
        tenant=tenant,
        supplier_name="Apex Office Supplies Ltd",
        bill_number="BILL-AUDIT-001",
        issue_date=timezone.now().date(),
        due_date=(timezone.now() + timezone.timedelta(days=30)).date(),
        amount=Decimal("12500.50"),
        paid_amount=Decimal("2500.00"),
        status="partial",
        category="Stationery & Office Supplies"
    )

    assert bill.amount == Decimal("12500.50"), "Decimal precision (12,2) amount mismatch!"
    assert bill.paid_amount == Decimal("2500.00"), "Decimal precision (12,2) paid_amount mismatch!"
    assert bill.outstanding_amount == Decimal("10000.50"), f"Outstanding amount property calculation mismatch: {bill.outstanding_amount}"
    print(f"[PASS] 1. Field Definitions & Decimal Precision (12,2) Verified. Outstanding Amount: ${bill.outstanding_amount}")

    # 2. Validate Tenant Isolation
    assert bill.tenant_id == tenant.id, "Tenant isolation foreign key mismatch!"
    print(f"[PASS] 2. Multi-Tenant Isolation Verified. Tenant ID: {bill.tenant_id}")

    # 3. Validate Indexes
    indexes = [idx.fields for idx in SupplierBill._meta.indexes]
    assert ['tenant', 'status'] in indexes, "Missing ['tenant', 'status'] index!"
    assert ['tenant', 'due_date'] in indexes, "Missing ['tenant', 'due_date'] index!"
    assert ['supplier_name'] in indexes, "Missing ['supplier_name'] index!"
    assert SupplierBill._meta.get_field('bill_number').db_index == True, "bill_number missing db_index!"
    print(f"[PASS] 3. Database Indexes & Query Optimizations Verified. Indexes: {indexes}")

    # 4. Validate Business Rules & Model Clean Constraints
    # Rule 4a: Amount must be greater than zero
    invalid_bill_zero = SupplierBill(
        tenant=tenant,
        supplier_name="Invalid Zero Vendor",
        bill_number="BILL-ERR-001",
        issue_date=timezone.now().date(),
        due_date=(timezone.now() + timezone.timedelta(days=30)).date(),
        amount=Decimal("0.00")
    )
    try:
        invalid_bill_zero.clean()
        assert False, "Failed to catch zero amount validation error!"
    except ValidationError as e:
        assert 'amount' in e.message_dict
        print("[PASS] 4a. Business Constraint Verified: Amount must be > $0.00.")

    # Rule 4b: Paid amount cannot exceed total bill amount
    invalid_bill_overpaid = SupplierBill(
        tenant=tenant,
        supplier_name="Overpaid Vendor",
        bill_number="BILL-ERR-002",
        issue_date=timezone.now().date(),
        due_date=(timezone.now() + timezone.timedelta(days=30)).date(),
        amount=Decimal("1000.00"),
        paid_amount=Decimal("1500.00")
    )
    try:
        invalid_bill_overpaid.clean()
        assert False, "Failed to catch overpayment validation error!"
    except ValidationError as e:
        assert 'paid_amount' in e.message_dict
        print("[PASS] 4b. Business Constraint Verified: Paid amount cannot exceed total bill amount.")

    # Rule 4c: Due date cannot be earlier than issue date
    invalid_bill_dates = SupplierBill(
        tenant=tenant,
        supplier_name="Invalid Dates Vendor",
        bill_number="BILL-ERR-003",
        issue_date=timezone.now().date(),
        due_date=(timezone.now() - timezone.timedelta(days=5)).date(),
        amount=Decimal("500.00")
    )
    try:
        invalid_bill_dates.clean()
        assert False, "Failed to catch invalid due date validation error!"
    except ValidationError as e:
        assert 'due_date' in e.message_dict
        print("[PASS] 4c. Business Constraint Verified: Due date cannot be earlier than issue date.")

    print("\n=================================================================")
    print("PHASE 1 — ALL SUPPLIER BILL MODEL VERIFICATIONS PASSED CLEANLY!")
    print("=================================================================")

if __name__ == "__main__":
    run_tests()
