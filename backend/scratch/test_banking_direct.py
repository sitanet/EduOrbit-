import os
import sys
import django

sys.path.insert(0, r"c:\Users\user\Desktop\Development\SMS")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.config.settings.local")
django.setup()

from decimal import Decimal
from django.utils import timezone

from backend.apps.tenants.models import Tenant
from backend.apps.efbm.models import BankAccount, BankStatementItem, ChequeRegister, Payment
from backend.apps.efbm.services import BankManagementService

def run_tests():
    print("--- Running Bank Management Direct Verification ---")

    tenant = Tenant.objects.first() or Tenant.objects.create(name="Banking Tenant Direct")

    account = BankAccount.objects.create(
        tenant=tenant,
        account_name="Main Operating Account",
        account_number="0123456789",
        bank_name="First National Bank",
        account_type="bank",
        opening_balance=Decimal("100000.00"),
        current_balance=Decimal("150000.00")
    )

    # 1. Test Statement Import
    lines = [
        {'date': timezone.now().date(), 'description': 'Fee Payment Direct', 'reference': 'PYMT-BANK-101', 'credit': '2500.00', 'debit': '0.00'}
    ]
    imported = BankManagementService.import_bank_statement(account_id=account.id, statement_lines=lines)
    assert len(imported) == 1, "Bank statement import count mismatch!"
    print(f"[PASS] Bank Statement Import Verified. Imported: {len(imported)} lines")

    # 2. Create matching payment for auto reconciliation
    Payment.objects.create(
        tenant=tenant,
        amount=Decimal("2500.00"),
        payment_method="transfer",
        reference="PYMT-BANK-101"
    )

    # 3. Test Auto Reconciliation
    matched = BankManagementService.auto_reconcile_statement(account_id=account.id)
    assert matched == 1, "Auto reconciliation match count failure!"
    print(f"[PASS] Automated Bank Reconciliation Verified. Matched: {matched} items")

    # 4. Test Cheque Register
    cheque = ChequeRegister.objects.create(
        tenant=tenant,
        bank_account=account,
        cheque_number="CHQ-88001",
        payee_name="Utility Corp",
        amount=Decimal("450.00"),
        status="issued"
    )
    cheques = BankManagementService.get_cheque_register(account_id=account.id)
    assert len(cheques) >= 1, "Cheque register retrieval failure!"
    print(f"[PASS] Cheque Register Verified. Cheque #{cheque.cheque_number} registered.")

    # 5. Test Cashbook Report
    cashbook = BankManagementService.get_cashbook_report(tenant=tenant)
    assert len(cashbook) >= 1, "Cashbook report transaction count mismatch!"
    print(f"[PASS] Cashbook Statement Verified. Total transactions logged: {len(cashbook)}")

    # 6. Test Bank Dashboard Metrics
    metrics = BankManagementService.get_bank_dashboard_widgets(tenant=tenant)
    assert metrics['total_bank_balance'] >= Decimal("150000.00"), "Bank dashboard metrics failure!"
    print(f"[PASS] Bank Dashboard Metrics Verified. Total Bank Balance: ${metrics['total_bank_balance']}")

    print("--- ALL BANK MANAGEMENT VERIFICATION TESTS PASSED CLEANLY! ---")

if __name__ == "__main__":
    run_tests()
