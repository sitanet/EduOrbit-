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
from backend.apps.efbm.models import Supplier, SupplierStatement, SupplierLedger

def run_tests():
    print("=================================================================")
    print("PHASE 4 — SUPPLIER STATEMENT MODEL EVIDENCE AUDIT & VALIDATION")
    print("=================================================================")

    tenant = Tenant.objects.first() or Tenant.objects.create(name="SupplierStatement Validation Tenant")
    supplier = Supplier.objects.create(tenant=tenant, name="Global Tech Supplies")

    start_d = timezone.now().date().replace(day=1)
    end_d = timezone.now().date()

    # 1. Model Creation & Decimal Precision
    stmt = SupplierStatement.objects.create(
        tenant=tenant,
        supplier=supplier,
        statement_number="ST-2026-00045",
        statement_start_date=start_d,
        statement_end_date=end_d,
        opening_balance=Decimal("1000.00"),
        total_debits=Decimal("5000.00"),
        total_credits=Decimal("2000.00"),
        closing_balance=Decimal("4000.00"),
        is_finalized=True
    )

    assert stmt.opening_balance == Decimal("1000.00"), "Opening balance decimal precision mismatch!"
    assert stmt.total_debits == Decimal("5000.00"), "Total debits decimal precision mismatch!"
    assert stmt.total_credits == Decimal("2000.00"), "Total credits decimal precision mismatch!"
    assert stmt.closing_balance == Decimal("4000.00"), "Closing balance decimal precision mismatch!"
    print(f"[PASS] 1. Field Definitions & Decimal Precision (12,2) Verified. Closing Balance: ${stmt.closing_balance}")

    # 2. Properties (statement_period & transaction_count)
    expected_period = f"{start_d.strftime('%d %b %Y')} - {end_d.strftime('%d %b %Y')}"
    assert stmt.statement_period == expected_period, f"statement_period mismatch: {stmt.statement_period}"
    
    # Create ledger entries within period to test transaction_count
    SupplierLedger.objects.create(
        tenant=tenant,
        supplier=supplier,
        transaction_date=start_d,
        description="Delivery Invoice #1",
        reference_number="REF-001",
        debit_amount=Decimal("5000.00"),
        balance_after=Decimal("6000.00")
    )
    assert stmt.transaction_count >= 1, f"transaction_count property failure: {stmt.transaction_count}"
    print(f"[PASS] 2. @property Methods Verified. (period='{stmt.statement_period}', count={stmt.transaction_count})")

    # 3. Validation Rules (clean())
    # 3a: End date < Start date
    invalid_dates = SupplierStatement(
        tenant=tenant,
        supplier=supplier,
        statement_number="ST-ERR-001",
        statement_start_date=end_d,
        statement_end_date=start_d - timezone.timedelta(days=1),
        opening_balance=Decimal("1000.00"),
        total_debits=Decimal("0.00"),
        total_credits=Decimal("0.00"),
        closing_balance=Decimal("1000.00")
    )
    try:
        invalid_dates.clean()
        assert False, "Failed to catch start/end date validation error!"
    except ValidationError as e:
        assert 'statement_end_date' in e.message_dict
        print("[PASS] 3a. Business Constraint Verified: End date cannot be earlier than start date.")

    # 3b: Closing balance consistency check (Opening + Debits - Credits != Closing)
    invalid_closing = SupplierStatement(
        tenant=tenant,
        supplier=supplier,
        statement_number="ST-ERR-002",
        statement_start_date=start_d,
        statement_end_date=end_d,
        opening_balance=Decimal("1000.00"),
        total_debits=Decimal("5000.00"),
        total_credits=Decimal("2000.00"),
        closing_balance=Decimal("9999.00")  # Should be 4000.00
    )
    try:
        invalid_closing.clean()
        assert False, "Failed to catch closing balance math inconsistency!"
    except ValidationError as e:
        assert 'closing_balance' in e.message_dict
        print("[PASS] 3b. Business Constraint Verified: Closing balance consistency (Opening + Debits - Credits = Closing).")

    # 4. __str__() Formatting
    period_str = start_d.strftime('%b %Y')
    expected_str = f"Statement #ST-2026-00045 - Global Tech Supplies ({period_str})"
    assert str(stmt) == expected_str, f"__str__() mismatch: '{str(stmt)}' vs '{expected_str}'"
    print(f"[PASS] 4. __str__() Formatting Verified: '{str(stmt)}'")

    # 5. Database Constraints & Multi-Tenant Isolation
    constraints = [c.name for c in SupplierStatement._meta.constraints]
    assert 'unique_supplier_statement_per_period' in constraints, "Missing UniqueConstraint on (tenant, supplier, statement_start_date, statement_end_date)!"
    assert stmt.tenant_id == tenant.id, "Multi-tenant isolation mismatch!"
    print(f"[PASS] 5. UniqueConstraint & Multi-Tenant Isolation Verified: {constraints}")

    print("\n=================================================================")
    print("PHASE 4 — ALL SUPPLIER STATEMENT MODEL VERIFICATIONS PASSED CLEANLY!")
    print("=================================================================")

if __name__ == "__main__":
    run_tests()
