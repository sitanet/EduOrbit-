import os
import sys
import django

sys.path.insert(0, r"c:\Users\user\Desktop\Development\SMS")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.config.settings.local")
django.setup()

from decimal import Decimal
from backend.apps.tenants.models import Tenant
from backend.apps.efbm.models import BankAccount
from backend.apps.efbm.services import ExecutiveAnalyticsService

def run_tests():
    print("--- Running Executive Financial Analytics Direct Verification ---")

    tenant = Tenant.objects.first() or Tenant.objects.create(name="Analytics Tenant Direct")

    BankAccount.objects.create(
        tenant=tenant,
        account_name="Executive Treasury Account",
        account_number="9988776655",
        bank_name="Apex Reserve Bank",
        account_type="bank",
        current_balance=Decimal("250000.00")
    )

    dashboard = ExecutiveAnalyticsService.get_executive_financial_dashboard(tenant=tenant)

    assert 'revenue' in dashboard, "Executive dashboard missing 'revenue' key!"
    assert 'expenses' in dashboard, "Executive dashboard missing 'expenses' key!"
    assert 'profit' in dashboard, "Executive dashboard missing 'profit' key!"
    assert 'cash_position' in dashboard, "Executive dashboard missing 'cash_position' key!"
    assert 'receivables' in dashboard, "Executive dashboard missing 'receivables' key!"
    assert 'payables' in dashboard, "Executive dashboard missing 'payables' key!"
    assert 'bank_balance' in dashboard, "Executive dashboard missing 'bank_balance' key!"
    assert 'monthly_collection' in dashboard, "Executive dashboard missing 'monthly_collection' key!"
    assert len(dashboard['chart_labels']) == 6, "Trend chart labels count mismatch!"
    assert len(dashboard['revenue_trend']) == 6, "Revenue trend data count mismatch!"
    assert len(dashboard['expense_trend']) == 6, "Expense trend data count mismatch!"

    print(f"[PASS] C-Suite Cards Verified. Bank Balance: ${dashboard['bank_balance']}, Cash Position: ${dashboard['cash_position']}")
    print(f"[PASS] 6-Month Revenue & Expense Trend Data Verified: Labels={dashboard['chart_labels']}")

    print("--- ALL EXECUTIVE FINANCIAL ANALYTICS VERIFICATION TESTS PASSED CLEANLY! ---")

if __name__ == "__main__":
    run_tests()
