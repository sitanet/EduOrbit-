import os
import sys
import django

sys.path.insert(0, r"c:\Users\user\Desktop\Development\SMS")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.config.settings.local")
django.setup()

from decimal import Decimal
from django.utils import timezone

from backend.apps.tenants.models import Tenant, School
from backend.apps.efbm.models import Invoice, Payment, JournalEvent, JournalEntry
from backend.apps.efbm.services import FinancialReportingService

def run_tests():
    print("--- Running Direct Financial Reporting Foundation Verification ---")

    tenant = Tenant.objects.first() or Tenant.objects.create(name="Financial Test Tenant Direct")
    school = School.objects.filter(tenant=tenant).first() or School.objects.create(tenant=tenant, name="Capital Academy Direct")

    event = JournalEvent.objects.create(
        tenant=tenant,
        event_type="test_fee_billing",
        timestamp=timezone.now()
    )
    JournalEntry.objects.create(
        tenant=tenant,
        event=event,
        account_name="Student Receivables",
        amount=Decimal("12500.00"),
        entry_type="debit"
    )
    JournalEntry.objects.create(
        tenant=tenant,
        event=event,
        account_name="Tuition Revenue",
        amount=Decimal("12500.00"),
        entry_type="credit"
    )

    # 1. Test Trial Balance
    tb = FinancialReportingService.get_trial_balance(tenant=tenant)
    assert tb['is_balanced'], "Trial balance is not balanced!"
    assert tb['total_debit'] == tb['total_credit'], "Trial balance total debit != credit"
    print(f"[PASS] Trial Balance Verified. Total Debits: ${tb['total_debit']}, Total Credits: ${tb['total_credit']}")

    # 2. Test Income Statement
    pnl = FinancialReportingService.get_income_statement(tenant=tenant)
    assert pnl['revenue'] >= Decimal("12500.00"), f"Income Statement Revenue mismatch: {pnl['revenue']}"
    assert pnl['net_profit'] > Decimal("0.00"), f"Income Statement Net Profit mismatch: {pnl['net_profit']}"
    print(f"[PASS] Income Statement Verified. Revenue: ${pnl['revenue']}, Net Profit: ${pnl['net_profit']}")

    # 3. Test Balance Sheet
    bs = FinancialReportingService.get_balance_sheet(tenant=tenant)
    assert bs['is_balanced'], f"Balance Sheet accounting equation failed! Assets (${bs['total_assets']}) != Liabilities+Equity (${bs['total_liabilities_equity']})"
    print(f"[PASS] Balance Sheet Verified. Assets: ${bs['total_assets']} = Liabilities + Equity: ${bs['total_liabilities_equity']}")

    print("--- ALL FINANCIAL REPORTING FOUNDATION VERIFICATION TESTS PASSED CLEANLY! ---")

if __name__ == "__main__":
    run_tests()
