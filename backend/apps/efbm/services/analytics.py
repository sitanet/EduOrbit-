from decimal import Decimal
from datetime import datetime, timedelta
from django.db.models import Sum
from django.utils import timezone

from backend.apps.efbm.models import Invoice, Payment, SupplierBill, SupplierPayment, BankAccount
from backend.apps.efbm.services.financial_reporting import FinancialReportingService


class ExecutiveAnalyticsService:
    """
    Enterprise Executive Financial Analytics Engine for EduOrbit ERP.
    Computes C-Suite Dashboard Cards: Revenue, Expenses, Net Profit, Cash Position,
    Receivables, Payables, Bank Liquidity, Monthly Collection, 6-Month Revenue & Expense Trends,
    and Interactive Chart Data with HTMX Live Refresh.
    """

    @classmethod
    def get_executive_financial_dashboard(cls, tenant):
        """
        Computes live database aggregates for the Executive Financial Dashboard.
        """
        pnl = FinancialReportingService.get_income_statement(tenant=tenant)
        bs = FinancialReportingService.get_balance_sheet(tenant=tenant)

        revenue = pnl['revenue']
        expenses = pnl['operating_expenses']
        profit = pnl['net_profit']

        # Bank & Cash Balances
        accounts = BankAccount.objects.all()
        if tenant:
            accounts = accounts.filter(tenant=tenant)

        bank_balance = sum(acc.current_balance for acc in accounts if acc.account_type == 'bank')
        cash_position = sum(acc.current_balance for acc in accounts if acc.account_type == 'cash') + bank_balance

        # Receivables & Payables
        invoices = Invoice.objects.filter(status__in=['issued', 'partial'])
        if tenant:
            invoices = invoices.filter(tenant=tenant)

        receivables = Decimal('0.00')
        for inv in invoices:
            tot_items = inv.items.aggregate(tot=Sum('amount'))['tot'] or Decimal('0.00')
            tot_paid = Payment.objects.filter(invoice=inv).aggregate(tot=Sum('amount'))['tot'] or Decimal('0.00')
            receivables += (tot_items - tot_paid)

        bills = SupplierBill.objects.filter(status__in=['pending', 'approved', 'partial'])
        if tenant:
            bills = bills.filter(tenant=tenant)

        payables = sum(b.outstanding_amount for b in bills)

        # Monthly Collections (Current Month)
        now = timezone.now()
        first_day_month = now.replace(day=1).date()
        
        month_payments = Payment.objects.filter(payment_date__date__gte=first_day_month)
        if tenant:
            month_payments = month_payments.filter(tenant=tenant)

        monthly_collection = month_payments.aggregate(tot=Sum('amount'))['tot'] or Decimal('0.00')

        # 6-Month Revenue & Expense Trends
        revenue_trend = []
        expense_trend = []
        labels = []

        for i in range(5, -1, -1):
            target_month = now - timedelta(days=i * 30)
            month_str = target_month.strftime('%b %Y')
            labels.append(month_str)

            # Monthly Payments Received
            m_start = target_month.replace(day=1).date()
            m_end = (target_month.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
            
            pymts = Payment.objects.filter(payment_date__date__gte=m_start, payment_date__date__lte=m_end)
            disbs = SupplierPayment.objects.filter(payment_date__date__gte=m_start, payment_date__date__lte=m_end)
            if tenant:
                pymts = pymts.filter(tenant=tenant)
                disbs = disbs.filter(tenant=tenant)

            rev_val = float(pymts.aggregate(tot=Sum('amount'))['tot'] or Decimal('0.00'))
            exp_val = float(disbs.aggregate(tot=Sum('amount'))['tot'] or Decimal('0.00'))

            revenue_trend.append(rev_val)
            expense_trend.append(exp_val)

        return {
            'revenue': revenue,
            'expenses': expenses,
            'profit': profit,
            'cash_position': cash_position,
            'receivables': receivables,
            'payables': payables,
            'bank_balance': bank_balance,
            'monthly_collection': monthly_collection,
            'chart_labels': labels,
            'revenue_trend': revenue_trend,
            'expense_trend': expense_trend
        }
