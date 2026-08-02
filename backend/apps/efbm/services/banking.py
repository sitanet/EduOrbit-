from decimal import Decimal
from django.db import transaction
from django.db.models import Sum, Q
from django.utils import timezone

from backend.apps.efbm.models import BankAccount, BankStatementItem, ChequeRegister, Payment, SupplierPayment, JournalEntry


class BankManagementService:
    """
    Enterprise Bank Management Service for EduOrbit ERP.
    Handles Bank & Cash Accounts, Statement Importing, Automated & Manual Reconciliation,
    Outstanding Transactions, Cheque Register, Cashbook Reports, and Bank Dashboard Metrics.
    """

    @classmethod
    def get_bank_accounts(cls, tenant):
        """
        Retrieves all bank and cash treasury accounts.
        """
        accounts = BankAccount.objects.all()
        if tenant:
            accounts = accounts.filter(tenant=tenant)
        return accounts

    @classmethod
    @transaction.atomic
    def import_bank_statement(cls, account_id, statement_lines):
        """
        Imports bank statement lines into BankStatementItem.
        statement_lines: list of dicts [{'date', 'description', 'reference', 'debit', 'credit'}]
        """
        bank_acc = BankAccount.objects.get(id=account_id)
        imported_items = []

        for line in statement_lines:
            item = BankStatementItem.objects.create(
                tenant=bank_acc.tenant,
                bank_account=bank_acc,
                transaction_date=line.get('date', timezone.now().date()),
                description=line.get('description', ''),
                reference=line.get('reference', ''),
                debit_amount=Decimal(str(line.get('debit', '0.00'))),
                credit_amount=Decimal(str(line.get('credit', '0.00'))),
                is_reconciled=False
            )
            imported_items.append(item)

        return imported_items

    @classmethod
    @transaction.atomic
    def auto_reconcile_statement(cls, account_id):
        """
        Automatically matches un-reconciled BankStatementItems against system Payments by reference.
        """
        unreconciled = BankStatementItem.objects.filter(bank_account_id=account_id, is_reconciled=False)
        matched_count = 0

        for item in unreconciled:
            # 1. Match against Payment reference (Cash Inflows)
            if item.credit_amount > 0 and item.reference:
                match_pymt = Payment.objects.filter(reference__icontains=item.reference).first()
                if match_pymt:
                    item.is_reconciled = True
                    item.save()
                    matched_count += 1
                    continue

            # 2. Match against SupplierPayment reference (Cash Outflows)
            if item.debit_amount > 0 and item.reference:
                match_disb = SupplierPayment.objects.filter(reference__icontains=item.reference).first()
                if match_disb:
                    item.is_reconciled = True
                    item.save()
                    matched_count += 1
                    continue

        return matched_count

    @classmethod
    @transaction.atomic
    def manual_match_statement_item(cls, statement_item_id):
        """
        Manually marks a bank statement item as reconciled.
        """
        item = BankStatementItem.objects.get(id=statement_item_id)
        item.is_reconciled = True
        item.save()
        return item

    @classmethod
    def get_cheque_register(cls, account_id=None, tenant=None):
        """
        Retrieves cheque register logs.
        """
        cheques = ChequeRegister.objects.all()
        if tenant:
            cheques = cheques.filter(tenant=tenant)
        if account_id:
            cheques = cheques.filter(bank_account_id=account_id)
        return cheques.order_by('-issue_date')

    @classmethod
    def get_cashbook_report(cls, account_id=None, start_date=None, end_date=None, tenant=None):
        """
        Generates Cashbook statement detailing cash receipts and payments with running balance.
        """
        payments_in = Payment.objects.all()
        disbursements_out = SupplierPayment.objects.all()

        if tenant:
            payments_in = payments_in.filter(tenant=tenant)
            disbursements_out = disbursements_out.filter(tenant=tenant)

        if start_date:
            payments_in = payments_in.filter(payment_date__date__gte=start_date)
            disbursements_out = disbursements_out.filter(payment_date__date__gte=start_date)
        if end_date:
            payments_in = payments_in.filter(payment_date__date__lte=end_date)
            disbursements_out = disbursements_out.filter(payment_date__date__lte=end_date)

        transactions = []
        for pymt in payments_in:
            transactions.append({
                'date': pymt.payment_date,
                'type': 'Receipt',
                'reference': pymt.reference,
                'description': f"Student Payment ({pymt.payment_method})",
                'receipt': pymt.amount,
                'disbursement': Decimal('0.00')
            })

        for disb in disbursements_out:
            transactions.append({
                'date': disb.payment_date,
                'type': 'Disbursement',
                'reference': disb.reference,
                'description': f"Supplier Payment ({disb.payment_method})",
                'receipt': Decimal('0.00'),
                'disbursement': disb.amount
            })

        transactions.sort(key=lambda x: str(x['date']))

        running_balance = Decimal('0.00')
        cashbook_lines = []
        for t in transactions:
            running_balance += (t['receipt'] - t['disbursement'])
            t['running_balance'] = running_balance
            cashbook_lines.append(t)

        return cashbook_lines

    @classmethod
    def get_bank_dashboard_widgets(cls, tenant):
        """
        Live metrics for Bank Management Dashboard.
        """
        accounts = cls.get_bank_accounts(tenant=tenant)
        total_bank_balance = sum(acc.current_balance for acc in accounts if acc.account_type == 'bank')
        total_cash_balance = sum(acc.current_balance for acc in accounts if acc.account_type == 'cash')

        unreconciled_items = BankStatementItem.objects.filter(is_reconciled=False)
        if tenant:
            unreconciled_items = unreconciled_items.filter(tenant=tenant)
        unreconciled_count = unreconciled_items.count()

        cheques = ChequeRegister.objects.filter(status='issued')
        if tenant:
            cheques = cheques.filter(tenant=tenant)
        pending_cheques_count = cheques.count()

        return {
            'total_bank_balance': total_bank_balance,
            'total_cash_balance': total_cash_balance,
            'unreconciled_count': unreconciled_count,
            'pending_cheques_count': pending_cheques_count,
            'accounts': accounts
        }
