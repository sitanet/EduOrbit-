import os
import sys
import django

sys.path.insert(0, r"c:\Users\user\Desktop\Development\SMS")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.config.settings.local")
django.setup()

from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

from backend.apps.tenants.models import Tenant, School
from backend.apps.efbm.models import SupplierBill, SupplierPayment
from backend.apps.efbm.services import AccountsPayableService

def run_tests():
    print("--- Running Accounts Payable Direct Verification ---")

    tenant = Tenant.objects.first() or Tenant.objects.create(name="Payables Tenant Direct")
    
    bill = SupplierBill.objects.create(
        tenant=tenant,
        supplier_name="Apex IT Solutions",
        bill_number="BILL-AP-5001",
        issue_date=timezone.now().date(),
        due_date=(timezone.now() - timedelta(days=40)).date(), # 40 days overdue -> 31-60 bucket
        amount=Decimal("3500.00"),
        status="pending",
        category="IT Hardware"
    )

    # 1. Test Approval Workflow
    approved_bill = AccountsPayableService.approve_supplier_bill(bill_id=bill.id)
    assert approved_bill.status == "approved", "Supplier bill approval failed!"
    print(f"[PASS] Supplier Bill Approval Verified. Status: {approved_bill.status}")

    # 2. Test Disbursement Recording
    payment = AccountsPayableService.record_supplier_payment(
        bill_id=bill.id,
        amount=Decimal("1500.00"),
        payment_method="bank_transfer"
    )
    bill.refresh_from_db()
    assert bill.paid_amount == Decimal("1500.00"), "Supplier bill paid amount mismatch!"
    assert bill.status == "partial", "Supplier bill status mismatch!"
    print(f"[PASS] Supplier Payment Disbursement Verified. Paid: ${bill.paid_amount}, Remaining: ${bill.outstanding_amount}")

    # 3. Test Vendor Aging Report
    aging = AccountsPayableService.get_vendor_aging_report(tenant=tenant)
    assert aging['bucket_31_60'] >= Decimal("2000.00"), "Vendor aging bucket classification failure!"
    print(f"[PASS] Vendor Aging Analysis Verified. 31-60 Days Bucket: ${aging['bucket_31_60']}")

    # 4. Test Supplier Statement
    stmt = AccountsPayableService.get_supplier_statement(supplier_name="Apex IT Solutions", tenant=tenant)
    assert len(stmt['lines']) == 2, "Supplier statement transaction count mismatch!"
    assert stmt['ending_balance'] == Decimal("2000.00"), "Supplier statement ending balance mismatch!"
    print(f"[PASS] Supplier Statement Verified. Ending Balance: ${stmt['ending_balance']}")

    # 5. Test Payables Dashboard Metrics
    metrics = AccountsPayableService.get_payables_dashboard_widgets(tenant=tenant)
    assert metrics['total_payables'] >= Decimal("2000.00"), "Payables dashboard metrics failure!"
    print(f"[PASS] Payables Dashboard Metrics Verified. Total Payables: ${metrics['total_payables']}")

    print("--- ALL ACCOUNTS PAYABLE VERIFICATION TESTS PASSED CLEANLY! ---")

if __name__ == "__main__":
    run_tests()
