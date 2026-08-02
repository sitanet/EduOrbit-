import os
import sys
import django

sys.path.insert(0, r"c:\Users\user\Desktop\Development\SMS")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.config.settings.local")
django.setup()

from decimal import Decimal
from backend.apps.tenants.models import Tenant
from backend.apps.efbm.models import JournalEvent, JournalEntry, LedgerPosting
from backend.apps.efbm.services import AutomaticAccountingIntegrationService

def run_tests():
    print("--- Running Automatic Accounting Integrations Direct Verification ---")

    tenant = Tenant.objects.first() or Tenant.objects.create(name="Integration Test Tenant")
    ref = "REF-2026-TEST"

    # 1. Admissions
    event1 = AutomaticAccountingIntegrationService.post_admissions_application_fee(tenant, ref, Decimal("250.00"))
    assert event1.entries.count() == 2, "Admissions journal lines count mismatch!"
    print(f"[PASS] 1. Admissions Application Fee Posting Verified: {event1.event_type}")

    # Idempotency check: repeat posting should return existing event
    event1_repeat = AutomaticAccountingIntegrationService.post_admissions_application_fee(tenant, ref, Decimal("250.00"))
    assert event1_repeat.id == event1.id, "Admissions idempotency failure (duplicate created)!"
    print(f"[PASS] Admissions Idempotency Verified (No Duplicate).")

    # 2. School Fees
    event2 = AutomaticAccountingIntegrationService.post_school_fee_billing(tenant, ref, Decimal("5000.00"))
    assert event2.entries.count() == 2
    print(f"[PASS] 2. School Fee Billing Posting Verified: {event2.event_type}")

    # 3. Hostel
    event3 = AutomaticAccountingIntegrationService.post_hostel_fee_billing(tenant, ref, Decimal("1200.00"))
    assert event3.entries.count() == 2
    print(f"[PASS] 3. Hostel Fee Billing Posting Verified: {event3.event_type}")

    # 4. Transport
    event4 = AutomaticAccountingIntegrationService.post_transport_fee_billing(tenant, ref, Decimal("450.00"))
    assert event4.entries.count() == 2
    print(f"[PASS] 4. Transport Fee Billing Posting Verified: {event4.event_type}")

    # 5. Library
    event5 = AutomaticAccountingIntegrationService.post_library_fine_or_fee(tenant, ref, Decimal("25.00"))
    assert event5.entries.count() == 2
    print(f"[PASS] 5. Library Fine/Fee Posting Verified: {event5.event_type}")

    # 6. Clinic
    event6 = AutomaticAccountingIntegrationService.post_clinic_medical_fee(tenant, ref, Decimal("80.00"))
    assert event6.entries.count() == 2
    print(f"[PASS] 6. Clinic Medical Fee Posting Verified: {event6.event_type}")

    # 7. Payroll
    event7 = AutomaticAccountingIntegrationService.post_payroll_disbursement(tenant, ref, Decimal("15000.00"))
    assert event7.entries.count() == 2
    print(f"[PASS] 7. Payroll Disbursement Posting Verified: {event7.event_type}")

    # 8. Inventory
    event8 = AutomaticAccountingIntegrationService.post_inventory_purchase(tenant, ref, Decimal("3200.00"))
    assert event8.entries.count() == 2
    print(f"[PASS] 8. Inventory Purchase Posting Verified: {event8.event_type}")

    # 9. Purchasing
    event9 = AutomaticAccountingIntegrationService.post_purchasing_vendor_bill(tenant, ref, Decimal("1800.00"))
    assert event9.entries.count() == 2
    print(f"[PASS] 9. Purchasing Vendor Bill Posting Verified: {event9.event_type}")

    # 10. Asset Disposal
    event10 = AutomaticAccountingIntegrationService.post_asset_disposal(tenant, ref, Decimal("7500.00"))
    assert event10.entries.count() == 2
    print(f"[PASS] 10. Asset Disposal Posting Verified: {event10.event_type}")

    # 11. Refunds
    event11 = AutomaticAccountingIntegrationService.post_student_fee_refund(tenant, ref, Decimal("600.00"))
    assert event11.entries.count() == 2
    print(f"[PASS] 11. Student Fee Refund Posting Verified: {event11.event_type}")

    print("--- ALL 11 AUTOMATIC ACCOUNTING INTEGRATIONS PASSED CLEANLY! ---")

if __name__ == "__main__":
    run_tests()
