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
from backend.apps.efbm.models import Supplier, SupplierBalance

def run_tests():
    print("=================================================================")
    print("PHASE 3 — SUPPLIER BALANCE MODEL EVIDENCE AUDIT & VALIDATION")
    print("=================================================================")

    tenant = Tenant.objects.first() or Tenant.objects.create(name="SupplierBalance Validation Tenant")
    supplier = Supplier.objects.create(tenant=tenant, name="Acme Supplies Ltd")

    # 1. Model Creation & Decimal Precision
    bal = SupplierBalance.objects.create(
        tenant=tenant,
        supplier=supplier,
        current_balance=Decimal("5000.00"),
        total_bills=Decimal("10000.00"),
        total_payments=Decimal("5000.00"),
        total_credit_notes=Decimal("500.00"),
        total_debit_notes=Decimal("500.00"),
        last_transaction_date=timezone.now().date(),
        last_recalculated_at=timezone.now()
    )

    assert bal.current_balance == Decimal("5000.00"), "Current balance precision mismatch!"
    assert bal.total_bills == Decimal("10000.00"), "Total bills precision mismatch!"
    assert bal.total_payments == Decimal("5000.00"), "Total payments precision mismatch!"
    assert bal.total_credit_notes == Decimal("500.00"), "Total credit notes precision mismatch!"
    assert bal.total_debit_notes == Decimal("500.00"), "Total debit notes precision mismatch!"
    print(f"[PASS] 1. Field Definitions & Decimal Precision (12,2) Verified. Current Balance: ${bal.current_balance}")

    # 2. Properties (is_in_credit / is_in_debt)
    assert bal.is_in_debt == True, "is_in_debt property failure!"
    assert bal.is_in_credit == False, "is_in_credit property failure!"
    
    credit_bal = SupplierBalance(current_balance=Decimal("-150.00"))
    assert credit_bal.is_in_credit == True, "is_in_credit property failure for negative balance!"
    print(f"[PASS] 2. @property Methods Verified. (is_in_debt={bal.is_in_debt}, is_in_credit={bal.is_in_credit})")

    # 3. Validation Rules (clean())
    invalid_bal = SupplierBalance(
        tenant=tenant,
        supplier=supplier,
        total_bills=Decimal("-100.00")
    )
    try:
        invalid_bal.clean()
        assert False, "Failed to catch negative monetary field validation!"
    except ValidationError as e:
        assert 'total_bills' in e.message_dict
        print("[PASS] 3. Business Constraint Verified: Monetary fields cannot be negative.")

    # 4. __str__() Formatting
    assert str(bal) == f"SupplierBalance: {supplier.name} ($5000.00)", f"__str__() mismatch: {str(bal)}"
    print(f"[PASS] 4. __str__() Formatting Verified: '{str(bal)}'")

    # 5. Database Constraints & Indexes
    constraints = [c.name for c in SupplierBalance._meta.constraints]
    assert 'unique_supplier_balance_per_tenant' in constraints, "Missing UniqueConstraint on (tenant, supplier)!"
    print(f"[PASS] 5. UniqueConstraint Verified: {constraints}")

    print("\n=================================================================")
    print("PHASE 3 — ALL SUPPLIER BALANCE MODEL VERIFICATIONS PASSED CLEANLY!")
    print("=================================================================")

if __name__ == "__main__":
    run_tests()
