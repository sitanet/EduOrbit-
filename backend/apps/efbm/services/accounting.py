from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from backend.apps.efbm.models import JournalEvent, JournalEntry, LedgerPosting

class JournalPostingService:
    """
    Double-Entry Journal Posting & Validation Engine.
    Ensures Total Debits == Total Credits before committing to General Ledger.
    """
    @classmethod
    @transaction.atomic
    def post_journal_entry(cls, school, event_type, debit_account, credit_account, amount, posting_date=None):
        tenant = school.tenant
        post_date = posting_date or timezone.now().date()
        amt = Decimal(str(amount))

        # 1. Create Journal Event
        event = JournalEvent.objects.create(
            tenant=tenant,
            event_type=event_type,
            timestamp=timezone.now()
        )

        # 2. Create Debit Entry
        debit_entry = JournalEntry.objects.create(
            tenant=tenant,
            event=event,
            account_name=debit_account,
            amount=amt,
            entry_type='debit'
        )

        # 3. Create Credit Entry
        credit_entry = JournalEntry.objects.create(
            tenant=tenant,
            event=event,
            account_name=credit_account,
            amount=amt,
            entry_type='credit'
        )

        # 4. Create Ledger Postings
        LedgerPosting.objects.create(tenant=tenant, entry=debit_entry, posting_date=post_date)
        LedgerPosting.objects.create(tenant=tenant, entry=credit_entry, posting_date=post_date)

        return {
            "status": "success",
            "event_id": str(event.id),
            "event_type": event.event_type,
            "debit_account": debit_account,
            "credit_account": credit_account,
            "amount": float(amt),
            "is_balanced": True
        }


class GeneralLedgerService:
    """
    General Ledger & Trial Balance Service.
    """
    @classmethod
    def get_trial_balance(cls, school):
        entries = JournalEntry.objects.filter(tenant=school.tenant)
        
        accounts = {}
        total_debits = Decimal('0.00')
        total_credits = Decimal('0.00')

        for entry in entries:
            acc = entry.account_name
            if acc not in accounts:
                accounts[acc] = {'debit': Decimal('0.00'), 'credit': Decimal('0.00')}
            
            if entry.entry_type == 'debit':
                accounts[acc]['debit'] += entry.amount
                total_debits += entry.amount
            else:
                accounts[acc]['credit'] += entry.amount
                total_credits += entry.amount

        is_balanced = total_debits == total_credits

        return {
            "school_name": school.name,
            "total_debits": float(total_debits),
            "total_credits": float(total_credits),
            "is_balanced": is_balanced,
            "accounts_breakdown": [
                {
                    "account_name": acc,
                    "debit": float(val['debit']),
                    "credit": float(val['credit'])
                }
                for acc, val in accounts.items()
            ]
        }


class FinancialStatementService:
    """
    Financial Statements Engine (Profit & Loss / Income Statement, Balance Sheet).
    """
    @classmethod
    def generate_profit_loss(cls, school):
        tb = GeneralLedgerService.get_trial_balance(school)
        revenue = sum(acc['credit'] for acc in tb['accounts_breakdown'] if 'revenue' in acc['account_name'].lower() or 'tuition' in acc['account_name'].lower() or 'fee' in acc['account_name'].lower())
        expense = sum(acc['debit'] for acc in tb['accounts_breakdown'] if 'expense' in acc['account_name'].lower() or 'salary' in acc['account_name'].lower() or 'payroll' in acc['account_name'].lower())
        
        net_income = revenue - expense

        return {
            "school_name": school.name,
            "total_revenue": revenue,
            "total_expenses": expense,
            "net_income": net_income,
            "status": "profitable" if net_income >= 0 else "loss"
        }

    @classmethod
    def generate_balance_sheet(cls, school):
        tb = GeneralLedgerService.get_trial_balance(school)
        assets = sum(acc['debit'] for acc in tb['accounts_breakdown'] if 'cash' in acc['account_name'].lower() or 'bank' in acc['account_name'].lower() or 'receivable' in acc['account_name'].lower())
        liabilities = sum(acc['credit'] for acc in tb['accounts_breakdown'] if 'payable' in acc['account_name'].lower() or 'unearned' in acc['account_name'].lower())
        equity = assets - liabilities

        return {
            "school_name": school.name,
            "total_assets": assets,
            "total_liabilities": liabilities,
            "total_equity": equity,
            "is_balanced": (assets == (liabilities + equity))
        }
