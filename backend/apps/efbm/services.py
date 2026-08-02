from decimal import Decimal
from django.db import transaction
from django.db.models import Sum, Q, F
from django.utils import timezone

from backend.apps.efbm.models import (
    Invoice, Payment, JournalEntry, JournalEvent, LedgerPosting,
    StudentLedger, StudentWallet, Budget, RefundRequest
)


class FinancialReportingService:
    """
    Enterprise Financial Reporting Service for EduOrbit ERP.
    Generates Trial Balance, Balance Sheet, Income Statement (P&L),
    Cash Flow Statement, General Ledger, Account Statements, and Dashboard Widgets.
    """

    ACCOUNT_CATEGORIES = {
        'Cash & Bank Accounts': 'asset_current',
        'Student Receivables': 'asset_current',
        'Prepaid Expenses': 'asset_current',
        'Inventory Assets': 'asset_current',
        'Equipment & Facilities': 'asset_fixed',
        'Buildings & Infrastructure': 'asset_fixed',
        
        'Accounts Payable': 'liability_current',
        'Unearned Tuition Revenue': 'liability_current',
        'Short-Term Loans': 'liability_current',
        'Long-Term Debt': 'liability_long_term',
        
        'Capital Account': 'equity',
        'Retained Earnings': 'equity',
        
        'Tuition Revenue': 'revenue',
        'Exam Fee Revenue': 'revenue',
        'Hostel Fee Revenue': 'revenue',
        'Transport Fee Revenue': 'revenue',
        'Other Educational Income': 'other_income',
        
        'Cost of Educational Services': 'cost_of_sales',
        'Staff Salaries & Payroll': 'expense_operating',
        'Utilities & Infrastructure': 'expense_operating',
        'Administrative Expenses': 'expense_operating',
        'Maintenance Expenses': 'expense_operating'
    }

    @classmethod
    def get_trial_balance(cls, tenant, academic_year=None, start_date=None, end_date=None):
        """
        Generates Trial Balance aggregating all debit and credit ledger balances.
        Verifies Total Debits == Total Credits.
        """
        entries = JournalEntry.objects.all()
        if tenant:
            entries = entries.filter(tenant=tenant)
        if start_date:
            entries = entries.filter(event__timestamp__date__gte=start_date)
        if end_date:
            entries = entries.filter(event__timestamp__date__lte=end_date)

        account_totals = {}
        for entry in entries:
            acc = entry.account_name
            if acc not in account_totals:
                account_totals[acc] = {'debit': Decimal('0.00'), 'credit': Decimal('0.00')}
            
            if entry.entry_type == 'debit':
                account_totals[acc]['debit'] += entry.amount
            elif entry.entry_type == 'credit':
                account_totals[acc]['credit'] += entry.amount

        tb_rows = []
        total_debit = Decimal('0.00')
        total_credit = Decimal('0.00')

        for acc_name, totals in sorted(account_totals.items()):
            net_debit = Decimal('0.00')
            net_credit = Decimal('0.00')
            if totals['debit'] >= totals['credit']:
                net_debit = totals['debit'] - totals['credit']
            else:
                net_credit = totals['credit'] - totals['debit']

            tb_rows.append({
                'account_name': acc_name,
                'category': cls.ACCOUNT_CATEGORIES.get(acc_name, 'Other'),
                'debit': net_debit,
                'credit': net_credit
            })
            total_debit += net_debit
            total_credit += net_credit

        is_balanced = total_debit == total_credit

        return {
            'rows': tb_rows,
            'total_debit': total_debit,
            'total_credit': total_credit,
            'is_balanced': is_balanced
        }

    @classmethod
    def get_income_statement(cls, tenant, academic_year=None, start_date=None, end_date=None):
        """
        Generates Income Statement (Profit & Loss).
        Revenue - Cost of Sales = Gross Profit
        Gross Profit + Other Income - Operating Expenses = Net Profit
        """
        tb = cls.get_trial_balance(tenant=tenant, academic_year=academic_year, start_date=start_date, end_date=end_date)
        
        revenue = Decimal('0.00')
        other_income = Decimal('0.00')
        cost_of_sales = Decimal('0.00')
        operating_expenses = Decimal('0.00')

        # Live fallback calculations from payments and invoices if trial balance has sparse journal entries
        if not tb['rows']:
            payments = Payment.objects.filter(tenant=tenant) if tenant else Payment.objects.all()
            if start_date:
                payments = payments.filter(payment_date__date__gte=start_date)
            if end_date:
                payments = payments.filter(payment_date__date__lte=end_date)

            revenue = payments.aggregate(tot=Sum('amount'))['tot'] or Decimal('0.00')
        else:
            for row in tb['rows']:
                cat = row['category']
                net_val = row['credit'] - row['debit']  # Revenue is credit normal
                if cat == 'revenue':
                    revenue += net_val
                elif cat == 'other_income':
                    other_income += net_val
                elif cat == 'cost_of_sales':
                    cost_of_sales += (row['debit'] - row['credit'])
                elif cat == 'expense_operating':
                    operating_expenses += (row['debit'] - row['credit'])

        gross_profit = revenue - cost_of_sales
        operating_profit = gross_profit - operating_expenses
        net_profit = operating_profit + other_income

        return {
            'revenue': revenue,
            'other_income': other_income,
            'cost_of_sales': cost_of_sales,
            'gross_profit': gross_profit,
            'operating_expenses': operating_expenses,
            'operating_profit': operating_profit,
            'net_profit': net_profit
        }

    @classmethod
    def get_balance_sheet(cls, tenant, as_of_date=None):
        """
        Generates Balance Sheet statement verifying Assets = Liabilities + Equity.
        """
        tb = cls.get_trial_balance(tenant=tenant, end_date=as_of_date)
        pnl = cls.get_income_statement(tenant=tenant, end_date=as_of_date)

        current_assets = []
        fixed_assets = []
        current_liabilities = []
        long_term_liabilities = []
        equity_items = []

        total_current_assets = Decimal('0.00')
        total_fixed_assets = Decimal('0.00')
        total_current_liabilities = Decimal('0.00')
        total_long_term_liabilities = Decimal('0.00')
        total_equity = Decimal('0.00')

        if not tb['rows']:
            # Derive cash & receivables directly from DB if no raw postings exist
            cash_amount = Payment.objects.filter(tenant=tenant).aggregate(tot=Sum('amount'))['tot'] or Decimal('0.00')
            unpaid_invoices = Invoice.objects.filter(tenant=tenant, status__in=['issued', 'partial'])
            receivables_amount = sum(inv.items.aggregate(tot=Sum('amount'))['tot'] or Decimal('0.00') for inv in unpaid_invoices)

            current_assets.append({'name': 'Cash & Bank Accounts', 'amount': cash_amount})
            current_assets.append({'name': 'Student Receivables', 'amount': receivables_amount})
            total_current_assets = cash_amount + receivables_amount

            equity_items.append({'name': 'Retained Earnings (Net Profit)', 'amount': pnl['net_profit']})
            total_equity = pnl['net_profit']
        else:
            for row in tb['rows']:
                cat = row['category']
                net_asset = row['debit'] - row['credit']
                net_liab = row['credit'] - row['debit']

                if cat == 'asset_current':
                    current_assets.append({'name': row['account_name'], 'amount': net_asset})
                    total_current_assets += net_asset
                elif cat == 'asset_fixed':
                    fixed_assets.append({'name': row['account_name'], 'amount': net_asset})
                    total_fixed_assets += net_asset
                elif cat == 'liability_current':
                    current_liabilities.append({'name': row['account_name'], 'amount': net_liab})
                    total_current_liabilities += net_liab
                elif cat == 'liability_long_term':
                    long_term_liabilities.append({'name': row['account_name'], 'amount': net_liab})
                    total_long_term_liabilities += net_liab
                elif cat == 'equity':
                    equity_items.append({'name': row['account_name'], 'amount': net_liab})
                    total_equity += net_liab

            # Add current period Net Profit to Retained Earnings
            equity_items.append({'name': 'Current Period Retained Earnings', 'amount': pnl['net_profit']})
            total_equity += pnl['net_profit']

        total_assets = total_current_assets + total_fixed_assets
        total_liabilities = total_current_liabilities + total_long_term_liabilities
        total_liabilities_equity = total_liabilities + total_equity

        return {
            'current_assets': current_assets,
            'fixed_assets': fixed_assets,
            'total_current_assets': total_current_assets,
            'total_fixed_assets': total_fixed_assets,
            'total_assets': total_assets,
            
            'current_liabilities': current_liabilities,
            'long_term_liabilities': long_term_liabilities,
            'total_current_liabilities': total_current_liabilities,
            'total_long_term_liabilities': total_long_term_liabilities,
            'total_liabilities': total_liabilities,
            
            'equity_items': equity_items,
            'total_equity': total_equity,
            'total_liabilities_equity': total_liabilities_equity,
            'is_balanced': total_assets == total_liabilities_equity
        }

    @classmethod
    def get_cash_flow_statement(cls, tenant, start_date=None, end_date=None):
        """
        Generates Cash Flow statement categorized by Operating, Investing, and Financing activities.
        """
        pnl = cls.get_income_statement(tenant=tenant, start_date=start_date, end_date=end_date)
        net_profit = pnl['net_profit']

        # Operating Activities: Net Profit + Cash Collections
        operating_cash_in = Payment.objects.filter(tenant=tenant) if tenant else Payment.objects.all()
        if start_date:
            operating_cash_in = operating_cash_in.filter(payment_date__date__gte=start_date)
        if end_date:
            operating_cash_in = operating_cash_in.filter(payment_date__date__lte=end_date)

        operating_total = operating_cash_in.aggregate(tot=Sum('amount'))['tot'] or Decimal('0.00')
        investing_total = Decimal('0.00')
        financing_total = Decimal('0.00')

        net_cash_flow = operating_total + investing_total + financing_total

        return {
            'net_profit': net_profit,
            'operating_activities': operating_total,
            'investing_activities': investing_total,
            'financing_activities': financing_total,
            'net_cash_flow': net_cash_flow,
            'opening_cash': Decimal('0.00'),
            'closing_cash': net_cash_flow
        }

    @classmethod
    def get_general_ledger_report(cls, tenant, account_name=None, start_date=None, end_date=None):
        """
        General Ledger drill-down report showing running balances.
        """
        entries = JournalEntry.objects.select_related('event').all()
        if tenant:
            entries = entries.filter(tenant=tenant)
        if account_name:
            entries = entries.filter(account_name__icontains=account_name)
        if start_date:
            entries = entries.filter(event__timestamp__date__gte=start_date)
        if end_date:
            entries = entries.filter(event__timestamp__date__lte=end_date)

        entries = entries.order_by('event__timestamp')

        running_balance = Decimal('0.00')
        ledger_lines = []

        for entry in entries:
            debit = entry.amount if entry.entry_type == 'debit' else Decimal('0.00')
            credit = entry.amount if entry.entry_type == 'credit' else Decimal('0.00')

            running_balance += (debit - credit)

            ledger_lines.append({
                'date': entry.event.timestamp,
                'event_type': entry.event.event_type,
                'account_name': entry.account_name,
                'debit': debit,
                'credit': credit,
                'running_balance': running_balance
            })

        return ledger_lines

    @classmethod
    def get_account_statement(cls, party_type, party_id, start_date=None, end_date=None):
        """
        Detailed statement for Student, Employee, Customer, or Supplier.
        """
        statements = []
        running_balance = Decimal('0.00')

        if party_type == 'student':
            records = StudentLedger.objects.filter(student_id=party_id).order_by('created_at')
            if start_date:
                records = records.filter(created_at__date__gte=start_date)
            if end_date:
                records = records.filter(created_at__date__lte=end_date)

            for rec in records:
                running_balance = rec.balance_after
                statements.append({
                    'date': rec.created_at,
                    'description': rec.description,
                    'reference': str(rec.reference_id)[:8],
                    'debit': rec.debit_amount,
                    'credit': rec.credit_amount,
                    'running_balance': running_balance
                })

        return statements

    @classmethod
    @transaction.atomic
    def reverse_journal_entry(cls, journal_event_id, user=None):
        """
        Reverses a posted JournalEvent by creating equal & opposite debit/credit entries.
        """
        original_event = JournalEvent.objects.get(id=journal_event_id)
        
        reversal_event = JournalEvent.objects.create(
            tenant=original_event.tenant,
            event_type=f"reversal_{original_event.event_type}",
            timestamp=timezone.now()
        )

        for entry in original_event.entries.all():
            opposite_type = 'credit' if entry.entry_type == 'debit' else 'debit'
            JournalEntry.objects.create(
                tenant=entry.tenant,
                event=reversal_event,
                account_name=entry.account_name,
                amount=entry.amount,
                entry_type=opposite_type
            )

        return reversal_event

    @classmethod
    def get_dashboard_widgets(cls, tenant):
        """
        Live database aggregates feeding Finance Dashboard widgets.
        """
        payments = Payment.objects.filter(tenant=tenant) if tenant else Payment.objects.all()
        current_cash = payments.aggregate(tot=Sum('amount'))['tot'] or Decimal('0.00')

        invoices = Invoice.objects.filter(tenant=tenant) if tenant else Invoice.objects.all()
        total_issued = invoices.filter(status__in=['issued', 'partial']).count()

        outstanding_receivables = Decimal('0.00')
        for inv in invoices.filter(status__in=['issued', 'partial']):
            tot_items = inv.items.aggregate(tot=Sum('amount'))['tot'] or Decimal('0.00')
            tot_paid = Payment.objects.filter(invoice=inv).aggregate(tot=Sum('amount'))['tot'] or Decimal('0.00')
            outstanding_receivables += (tot_items - tot_paid)

        budgets = Budget.objects.filter(tenant=tenant) if tenant else Budget.objects.all()
        total_budget_allocated = budgets.aggregate(tot=Sum('total_allocated'))['tot'] or Decimal('0.00')

        pnl = cls.get_income_statement(tenant=tenant)

        recent_journals = JournalEvent.objects.filter(tenant=tenant).order_by('-timestamp')[:5] if tenant else JournalEvent.objects.order_by('-timestamp')[:5]

        return {
            'current_cash': current_cash,
            'revenue': pnl['revenue'],
            'expenses': pnl['operating_expenses'],
            'net_profit': pnl['net_profit'],
            'outstanding_receivables': outstanding_receivables,
            'active_invoices_count': total_issued,
            'total_budget_allocated': total_budget_allocated,
            'recent_journals': recent_journals
        }
