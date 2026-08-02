from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from backend.apps.tenants.models import School
from backend.apps.efbm.models import Invoice, StudentWallet

class EFBMDashboardWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        schools = School.objects.filter(tenant=getattr(request, 'tenant', None))
        active_school = schools.first()
        
        invoices = Invoice.objects.filter(student__current_school=active_school, tenant=getattr(request, 'tenant', None)).select_related('student__person')
        context = {
            'schools': schools,
            'active_school': active_school,
            'invoices': invoices
        }
        return render(request, 'efbm/dashboard.html', context)


class ParentWalletWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        wallets = StudentWallet.objects.filter(tenant=getattr(request, 'tenant', None)).select_related('parent')
        return render(request, 'efbm/wallet.html', {'wallets': wallets})


class TrialBalanceWebView(View):
    """
    Trial Balance Financial Statement Web View.
    """
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        tenant = getattr(request, 'tenant', None)
        from backend.apps.efbm.services import FinancialReportingService
        tb = FinancialReportingService.get_trial_balance(tenant=tenant)
        
        context = {'tb': tb}
        return render(request, 'efbm/reports/trial_balance.html', context)


class BalanceSheetWebView(View):
    """
    Balance Sheet Financial Statement Web View.
    """
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        tenant = getattr(request, 'tenant', None)
        from backend.apps.efbm.services import FinancialReportingService
        bs = FinancialReportingService.get_balance_sheet(tenant=tenant)
        
        context = {'bs': bs}
        return render(request, 'efbm/reports/balance_sheet.html', context)


class IncomeStatementWebView(View):
    """
    Income Statement (Profit & Loss) Web View.
    """
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        tenant = getattr(request, 'tenant', None)
        from backend.apps.efbm.services import FinancialReportingService
        pnl = FinancialReportingService.get_income_statement(tenant=tenant)
        
        context = {'pnl': pnl}
        return render(request, 'efbm/reports/income_statement.html', context)


class CashFlowWebView(View):
    """
    Cash Flow Statement Web View.
    """
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        tenant = getattr(request, 'tenant', None)
        from backend.apps.efbm.services import FinancialReportingService
        cf = FinancialReportingService.get_cash_flow_statement(tenant=tenant)
        
        context = {'cf': cf}
        return render(request, 'efbm/reports/cash_flow.html', context)


class GeneralLedgerWebView(View):
    """
    General Ledger Drill-down Web View.
    """
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        tenant = getattr(request, 'tenant', None)
        account_name = request.GET.get('account')
        from backend.apps.efbm.services import FinancialReportingService
        ledger = FinancialReportingService.get_general_ledger_report(tenant=tenant, account_name=account_name)
        
        context = {'ledger': ledger, 'account_name': account_name}
        return render(request, 'efbm/reports/general_ledger.html', context)


class AccountStatementWebView(View):
    """
    Account Statement Web View for Students, Employees, Customers, or Suppliers.
    """
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        party_type = request.GET.get('party_type', 'student')
        party_id = request.GET.get('party_id')
        from backend.apps.efbm.services import FinancialReportingService
        statement = FinancialReportingService.get_account_statement(party_type=party_type, party_id=party_id) if party_id else []
        
        context = {'statement': statement, 'party_type': party_type}
        return render(request, 'efbm/reports/account_statement.html', context)


class JournalReportWebView(View):
    """
    Journal Event Log & Reversal Web View.
    """
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        tenant = getattr(request, 'tenant', None)
        from backend.apps.efbm.models import JournalEvent
        events = JournalEvent.objects.filter(tenant=tenant).prefetch_related('entries') if tenant else JournalEvent.objects.prefetch_related('entries').all()
        
        context = {'events': events}
        return render(request, 'efbm/reports/journals.html', context)

    def post(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        event_id = request.POST.get('reverse_event_id')
        if event_id:
            from backend.apps.efbm.services import FinancialReportingService
            FinancialReportingService.reverse_journal_entry(journal_event_id=event_id, user=request.user)
            
        return redirect('journal_report_web')


class ChartOfAccountsWebView(View):
    """
    Interactive Chart of Accounts Browser & Tree View.
    """
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        tenant = getattr(request, 'tenant', None)
        from backend.apps.efbm.services import FinancialReportingService
        categories = FinancialReportingService.ACCOUNT_CATEGORIES
        search_query = request.GET.get('q', '').strip().lower()

        tree = {}
        for acc_name, cat in categories.items():
            if search_query and search_query not in acc_name.lower():
                continue
            if cat not in tree:
                tree[cat] = []
            tree[cat].append(acc_name)

        context = {'tree': tree, 'categories': categories, 'search_query': search_query}
        return render(request, 'efbm/reports/chart_of_accounts.html', context)


class ReceivablesDashboardWebView(View):
    """
    Accounts Receivable Workspace & Metric Dashboard View.
    """
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        tenant = getattr(request, 'tenant', None)
        from backend.apps.efbm.services import AccountsReceivableService
        metrics = AccountsReceivableService.get_receivables_dashboard_widgets(tenant=tenant)
        
        context = {'metrics': metrics}
        return render(request, 'efbm/receivables/dashboard.html', context)


class OutstandingInvoicesWebView(View):
    """
    Unpaid & Overdue Invoices Management View.
    """
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        tenant = getattr(request, 'tenant', None)
        from backend.apps.efbm.services import AccountsReceivableService
        invoices = AccountsReceivableService.get_outstanding_invoices(tenant=tenant)
        
        context = {'invoices': invoices}
        return render(request, 'efbm/receivables/outstanding_invoices.html', context)


class InvoiceAgingWebView(View):
    """
    Invoice Aging Analysis (0-30, 31-60, 61-90, 90+ days) View.
    """
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        tenant = getattr(request, 'tenant', None)
        from backend.apps.efbm.services import AccountsReceivableService
        aging = AccountsReceivableService.get_invoice_aging_report(tenant=tenant)
        
        context = {'aging': aging}
        return render(request, 'efbm/receivables/invoice_aging.html', context)


class PaymentHistoryWebView(View):
    """
    Settlement & Cash Collection Log View.
    """
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        tenant = getattr(request, 'tenant', None)
        from backend.apps.efbm.services import AccountsReceivableService
        payments = AccountsReceivableService.get_payment_history(tenant=tenant)
        
        context = {'payments': payments}
        return render(request, 'efbm/receivables/payment_history.html', context)


class PayablesDashboardWebView(View):
    """
    Accounts Payable Workspace & Vendor Management View.
    """
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        tenant = getattr(request, 'tenant', None)
        from backend.apps.efbm.services import AccountsPayableService
        metrics = AccountsPayableService.get_payables_dashboard_widgets(tenant=tenant)
        
        context = {'metrics': metrics}
        return render(request, 'efbm/payables/dashboard.html', context)


class SupplierBillsWebView(View):
    """
    Supplier Invoices & Bill Approval View.
    """
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        tenant = getattr(request, 'tenant', None)
        status_filter = request.GET.get('status')
        from backend.apps.efbm.services import AccountsPayableService
        bills = AccountsPayableService.get_supplier_bills(tenant=tenant, status=status_filter)
        
        context = {'bills': bills, 'status_filter': status_filter}
        return render(request, 'efbm/payables/supplier_bills.html', context)

    def post(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        action = request.POST.get('action')
        bill_id = request.POST.get('bill_id')

        from backend.apps.efbm.services.payables import SupplierPaymentService
        from backend.apps.core.models import Person

        tenant = getattr(request, 'tenant', None)
        
        if action == 'pay' and bill_id and tenant:
            amount = request.POST.get('amount')
            payment_method = request.POST.get('payment_method', 'bank_transfer')
            description = request.POST.get('description', '')
            
            # Get the Person record for the current user
            person = Person.objects.filter(user=request.user, tenant=tenant).first()
            
            # Create payment in draft status
            payment = SupplierPaymentService.create_payment(
                tenant=tenant,
                bill_id=bill_id,
                amount=amount,
                payment_method=payment_method,
                description=description,
                prepared_by=person
            )

        return redirect('supplier_bills_web')


class VendorAgingWebView(View):
    """
    Vendor Debt Aging Analysis View.
    """
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        tenant = getattr(request, 'tenant', None)
        from backend.apps.efbm.services.payables import AccountsPayableService
        aging = AccountsPayableService.get_vendor_aging(tenant=tenant)

        context = {'aging': aging}
        return render(request, 'efbm/payables/vendor_aging.html', context)


class BankDashboardWebView(View):
    """
    Bank & Cash Treasury Management Workspace View.
    """
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        tenant = getattr(request, 'tenant', None)
        from backend.apps.efbm.services import BankManagementService
        metrics = BankManagementService.get_bank_dashboard_widgets(tenant=tenant)
        
        context = {'metrics': metrics}
        return render(request, 'efbm/banking/dashboard.html', context)


class BankReconciliationWebView(View):
    """
    Automated & Manual Bank Reconciliation Workspace View.
    """
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        tenant = getattr(request, 'tenant', None)
        account_id = request.GET.get('account_id')
        from backend.apps.efbm.services import BankManagementService
        accounts = BankManagementService.get_bank_accounts(tenant=tenant)
        active_account = accounts.filter(id=account_id).first() if account_id else accounts.first()

        unreconciled_items = active_account.statement_items.filter(is_reconciled=False) if active_account else []
        
        context = {
            'accounts': accounts,
            'active_account': active_account,
            'unreconciled_items': unreconciled_items
        }
        return render(request, 'efbm/banking/reconciliation.html', context)

    def post(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        action = request.POST.get('action')
        account_id = request.POST.get('account_id')
        item_id = request.POST.get('item_id')

        from backend.apps.efbm.services import BankManagementService

        if action == 'auto_reconcile' and account_id:
            BankManagementService.auto_reconcile_statement(account_id=account_id)
        elif action == 'manual_match' and item_id:
            BankManagementService.manual_match_statement_item(statement_item_id=item_id)

        return redirect(f"{request.path}?account_id={account_id if account_id else ''}")


class ChequeRegisterWebView(View):
    """
    Cheque Register View.
    """
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        tenant = getattr(request, 'tenant', None)
        from backend.apps.efbm.services import BankManagementService
        cheques = BankManagementService.get_cheque_register(tenant=tenant)
        
        context = {'cheques': cheques}
        return render(request, 'efbm/banking/cheque_register.html', context)


class CashbookWebView(View):
    """
    Cashbook Treasury Statement View.
    """
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        tenant = getattr(request, 'tenant', None)
        from backend.apps.efbm.services import BankManagementService
        cashbook = BankManagementService.get_cashbook_report(tenant=tenant)
        
        context = {'cashbook': cashbook}
        return render(request, 'efbm/banking/cashbook.html', context)


class BudgetDashboardWebView(View):
    """
    Budget Management Workspace & Forecast Dashboard View.
    """
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        tenant = getattr(request, 'tenant', None)
        from backend.apps.efbm.services import BudgetManagementService
        metrics = BudgetManagementService.get_budget_forecast_dashboard(tenant=tenant)
        
        context = {'metrics': metrics}
        return render(request, 'efbm/budgeting/dashboard.html', context)

    def post(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        action = request.POST.get('action')
        budget_id = request.POST.get('budget_id')

        from backend.apps.efbm.services import BudgetManagementService

        if action == 'approve' and budget_id:
            BudgetManagementService.approve_budget(budget_id=budget_id, user=request.user)

        return redirect('budget_dashboard_web')


class BudgetVsActualWebView(View):
    """
    Budget vs. Actual Variance Analysis View.
    """
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        tenant = getattr(request, 'tenant', None)
        budget_id = request.GET.get('budget_id')

        from backend.apps.efbm.services import BudgetManagementService
        budgets = BudgetManagementService.get_budgets(tenant=tenant)
        active_budget = budgets.filter(id=budget_id).first() if budget_id else budgets.first()

        report = BudgetManagementService.get_budget_vs_actual_report(budget_id=active_budget.id) if active_budget else None

        context = {
            'budgets': budgets,
            'active_budget': active_budget,
            'report': report
        }
        return render(request, 'efbm/budgeting/budget_vs_actual.html', context)


class ExecutiveAnalyticsWebView(View):
    """
    Executive Financial Analytics & C-Suite Dashboard View.
    Supports HTMX Live Refresh and Role-Based Access Control.
    """
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        tenant = getattr(request, 'tenant', None)
        from backend.apps.efbm.services import ExecutiveAnalyticsService
        analytics = ExecutiveAnalyticsService.get_executive_financial_dashboard(tenant=tenant)
        
        context = {'analytics': analytics}

        # HTMX partial refresh for live chart updates
        if request.headers.get('HX-Request'):
            return render(request, 'efbm/analytics/partials/metrics_cards.html', context)

        return render(request, 'efbm/analytics/executive_dashboard.html', context)


class CustomerLedgerWebView(View):
    """
    Customer & Student Ledger Transaction View.
    """
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        tenant = getattr(request, 'tenant', None)
        from backend.apps.efbm.services import AccountsReceivableService
        ledger = AccountsReceivableService.get_customer_ledger(tenant=tenant)

        context = {'ledger': ledger}
        return render(request, 'efbm/receivables/customer_ledger.html', context)


class CreditNoteWebView(View):
    """
    Credit Notes List & Issuance Workspace View.
    """
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        tenant = getattr(request, 'tenant', None)
        from backend.apps.efbm.models import CreditNote
        notes = CreditNote.objects.filter(tenant=tenant) if tenant else CreditNote.objects.all()

        context = {'notes': notes}
        return render(request, 'efbm/receivables/credit_notes.html', context)

    def post(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        invoice_id = request.POST.get('invoice_id')
        amount = request.POST.get('amount')
        reason = request.POST.get('reason')

        from backend.apps.efbm.services import AccountsReceivableService
        if invoice_id and amount:
            AccountsReceivableService.create_credit_note(invoice_id=invoice_id, amount=amount, reason=reason)

        return redirect('credit_notes_web')


class DebitNoteWebView(View):
    """
    Debit Notes List & Issuance Workspace View.
    """
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        tenant = getattr(request, 'tenant', None)
        from backend.apps.efbm.models import DebitNote
        notes = DebitNote.objects.filter(tenant=tenant) if tenant else DebitNote.objects.all()

        context = {'notes': notes}
        return render(request, 'efbm/receivables/debit_notes.html', context)

    def post(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        invoice_id = request.POST.get('invoice_id')
        amount = request.POST.get('amount')
        reason = request.POST.get('reason')

        from backend.apps.efbm.services import AccountsReceivableService
        if invoice_id and amount:
            AccountsReceivableService.create_debit_note(invoice_id=invoice_id, amount=amount, reason=reason)

        return redirect('debit_notes_web')


class BadDebtWriteOffWebView(View):
    """
    Bad Debt Provisioning & Write-Off Approval Workflow View.
    """
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        tenant = getattr(request, 'tenant', None)
        from backend.apps.efbm.models import BadDebtWriteOff
        write_offs = BadDebtWriteOff.objects.filter(tenant=tenant) if tenant else BadDebtWriteOff.objects.all()

        context = {'write_offs': write_offs}
        return render(request, 'efbm/receivables/bad_debts.html', context)

    def post(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        action = request.POST.get('action')
        write_off_id = request.POST.get('write_off_id')
        invoice_id = request.POST.get('invoice_id')
        amount = request.POST.get('amount')
        reason = request.POST.get('reason')

        from backend.apps.efbm.services import AccountsReceivableService

        if action == 'provision' and invoice_id and amount:
            AccountsReceivableService.provision_bad_debt(invoice_id=invoice_id, amount=amount, reason=reason)
        elif action == 'approve' and write_off_id:
            AccountsReceivableService.approve_write_off(write_off_id=write_off_id, user=request.user)

        return redirect('bad_debts_web')


class BalanceConfirmationWebView(View):
    """
    Auditor Customer & Parent Balance Confirmation Logs View.
    """
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        confirmations = CustomerBalanceConfirmation.objects.filter(tenant=tenant) if tenant else CustomerBalanceConfirmation.objects.all()

        context = {'confirmations': confirmations}
        return render(request, 'efbm/receivables/balance_confirmations.html', context)


class SupplierCreditNotesWebView(View):
    """
    Supplier Credit Notes Management View.
    Supports viewing credit notes and creating new supplier credit adjustments.
    """
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        tenant = getattr(request, 'tenant', None)
        from backend.apps.efbm.services import AccountsPayableService
        credit_notes = AccountsPayableService.get_supplier_credit_notes(tenant=tenant)
        
        context = {'credit_notes': credit_notes}
        return render(request, 'efbm/payables/credit_notes.html', context)

    def post(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        tenant = getattr(request, 'tenant', None)
        bill_id = request.POST.get('bill_id')
        amount = request.POST.get('amount')
        reason = request.POST.get('reason')

        from backend.apps.efbm.services import AccountsPayableService
        if bill_id and amount and reason:
            AccountsPayableService.create_credit_note(tenant=tenant, bill_id=bill_id, amount=amount, reason=reason)

        return redirect('supplier_credit_notes_web')












class SupplierCreditNoteListWebView(View):
    """
    Supplier Credit Notes List & Management View.
    """
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        tenant = getattr(request, 'tenant', None)
        status_filter = request.GET.get('status')
        bill_id = request.GET.get('bill_id')
        
        from backend.apps.efbm.services.supplier_credit_notes import SupplierCreditNoteService
        credit_notes = SupplierCreditNoteService.get_credit_notes(
            tenant=tenant,
            status=status_filter,
            bill_id=bill_id
        )
        
        from backend.apps.efbm.models import SupplierCreditNote
        context = {
            'credit_notes': credit_notes,
            'status_filter': status_filter,
            'status_choices': SupplierCreditNote.STATUS_CHOICES
        }
        return render(request, 'efbm/payables/supplier_credit_notes.html', context)


class SupplierCreditNoteCreateWebView(View):
    """
    Create Supplier Credit Note View.
    """
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        tenant = getattr(request, 'tenant', None)
        bill_id = request.GET.get('bill_id')
        
        from backend.apps.efbm.models import SupplierBill
        bills = SupplierBill.objects.filter(tenant=tenant, status__in=['approved', 'partial'])
        selected_bill = bills.filter(id=bill_id).first() if bill_id else None
        
        context = {
            'bills': bills,
            'selected_bill': selected_bill
        }
        return render(request, 'efbm/payables/supplier_credit_note_form.html', context)
    
    def post(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        tenant = getattr(request, 'tenant', None)
        bill_id = request.POST.get('bill_id')
        amount = request.POST.get('amount')
        reason = request.POST.get('reason')
        
        from backend.apps.efbm.services.supplier_credit_notes import SupplierCreditNoteService
        from django.contrib import messages
        
        try:
            from backend.apps.people.models import Person
            created_by = Person.objects.filter(user=request.user, tenant=tenant).first()
            
            credit_note = SupplierCreditNoteService.create_credit_note(
                tenant=tenant,
                bill_id=bill_id,
                amount=amount,
                reason=reason,
                created_by=created_by
            )
            messages.success(request, f'Credit note {credit_note.note_number} created successfully.')
            return redirect('supplier_credit_note_detail', credit_note_id=credit_note.id)
        except Exception as e:
            messages.error(request, f'Error creating credit note: {str(e)}')
            return redirect('supplier_credit_note_create')


class SupplierCreditNoteDetailWebView(View):
    """
    Supplier Credit Note Detail & Actions View.
    """
    def get(self, request, credit_note_id):
        if not request.user.is_authenticated:
            return redirect('login_web')

        tenant = getattr(request, 'tenant', None)
        from backend.apps.efbm.services.supplier_credit_notes import SupplierCreditNoteService
        
        try:
            credit_note = SupplierCreditNoteService.get_credit_note(credit_note_id, tenant)
            context = {'credit_note': credit_note}
            return render(request, 'efbm/payables/supplier_credit_note_detail.html', context)
        except Exception as e:
            from django.contrib import messages
            messages.error(request, f'Credit note not found: {str(e)}')
            return redirect('supplier_credit_notes')
    
    def post(self, request, credit_note_id):
        if not request.user.is_authenticated:
            return redirect('login_web')

        tenant = getattr(request, 'tenant', None)
        action = request.POST.get('action')
        
        from backend.apps.efbm.services.supplier_credit_notes import SupplierCreditNoteService
        from backend.apps.people.models import Person
        from django.contrib import messages
        
        try:
            person = Person.objects.filter(user=request.user, tenant=tenant).first()
            
            if action == 'submit':
                credit_note = SupplierCreditNoteService.submit_credit_note(
                    credit_note_id=credit_note_id,
                    tenant=tenant,
                    submitted_by=person
                )
                messages.success(request, f'Credit note {credit_note.note_number} submitted for approval.')
            
            elif action == 'approve':
                credit_note = SupplierCreditNoteService.approve_credit_note(
                    credit_note_id=credit_note_id,
                    tenant=tenant,
                    approved_by=person
                )
                messages.success(request, f'Credit note {credit_note.note_number} approved successfully.')
            
            elif action == 'reject':
                rejection_reason = request.POST.get('rejection_reason')
                credit_note = SupplierCreditNoteService.reject_credit_note(
                    credit_note_id=credit_note_id,
                    tenant=tenant,
                    rejected_by=person,
                    rejection_reason=rejection_reason
                )
                messages.warning(request, f'Credit note {credit_note.note_number} rejected.')
            
            elif action == 'cancel':
                credit_note = SupplierCreditNoteService.cancel_credit_note(
                    credit_note_id=credit_note_id,
                    tenant=tenant,
                    cancelled_by=person
                )
                messages.info(request, f'Credit note {credit_note.note_number} cancelled.')
            
            return redirect('supplier_credit_note_detail', credit_note_id=credit_note_id)
        
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
            return redirect('supplier_credit_note_detail', credit_note_id=credit_note_id)


class SupplierDebitNoteListWebView(View):
    """
    Supplier Debit Notes List & Management View.
    """
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        tenant = getattr(request, 'tenant', None)
        status_filter = request.GET.get('status')
        bill_id = request.GET.get('bill_id')
        
        from backend.apps.efbm.services.payables import SupplierDebitNoteService
        debit_notes = SupplierDebitNoteService.get_debit_notes(
            tenant=tenant,
            status=status_filter,
            bill_id=bill_id
        )
        
        from backend.apps.efbm.models import SupplierDebitNote
        context = {
            'debit_notes': debit_notes,
            'status_filter': status_filter,
            'status_choices': SupplierDebitNote.STATUS_CHOICES
        }
        return render(request, 'efbm/payables/supplier_debit_notes.html', context)


class SupplierDebitNoteCreateWebView(View):
    """
    Create Supplier Debit Note View.
    """
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        tenant = getattr(request, 'tenant', None)
        bill_id = request.GET.get('bill_id')
        
        from backend.apps.efbm.models import SupplierBill
        bills = SupplierBill.objects.filter(tenant=tenant, status__in=['pending', 'approved', 'partial'])
        selected_bill = bills.filter(id=bill_id).first() if bill_id else None
        
        context = {
            'bills': bills,
            'selected_bill': selected_bill
        }
        return render(request, 'efbm/payables/supplier_debit_note_form.html', context)
    
    def post(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        tenant = getattr(request, 'tenant', None)
        bill_id = request.POST.get('bill_id')
        amount = request.POST.get('amount')
        reason = request.POST.get('reason')
        description = request.POST.get('description', '')
        
        from backend.apps.efbm.services.payables import SupplierDebitNoteService
        from django.contrib import messages
        
        try:
            from backend.apps.people.models import Person
            created_by = Person.objects.filter(user=request.user, tenant=tenant).first()
            
            debit_note = SupplierDebitNoteService.create_debit_note(
                tenant=tenant,
                bill_id=bill_id,
                amount=amount,
                reason=reason,
                description=description,
                created_by=created_by
            )
            messages.success(request, f'Debit note {debit_note.debit_note_number} created successfully.')
            return redirect('supplier_debit_note_detail', debit_note_id=debit_note.id)
        except Exception as e:
            messages.error(request, f'Error creating debit note: {str(e)}')
            return redirect('supplier_debit_note_create')


class SupplierDebitNoteDetailWebView(View):
    """
    Supplier Debit Note Detail & Actions View.
    """
    def get(self, request, debit_note_id):
        if not request.user.is_authenticated:
            return redirect('login_web')

        tenant = getattr(request, 'tenant', None)
        from backend.apps.efbm.services.payables import SupplierDebitNoteService
        
        try:
            debit_note = SupplierDebitNoteService.get_debit_note(debit_note_id, tenant)
            context = {'debit_note': debit_note}
            return render(request, 'efbm/payables/supplier_debit_note_detail.html', context)
        except Exception as e:
            from django.contrib import messages
            messages.error(request, f'Debit note not found: {str(e)}')
            return redirect('supplier_debit_notes')
    
    def post(self, request, debit_note_id):
        if not request.user.is_authenticated:
            return redirect('login_web')

        tenant = getattr(request, 'tenant', None)
        action = request.POST.get('action')
        
        from backend.apps.efbm.services.payables import SupplierDebitNoteService
        from backend.apps.people.models import Person
        from django.contrib import messages
        
        try:
            person = Person.objects.filter(user=request.user, tenant=tenant).first()
            
            if action == 'submit':
                debit_note = SupplierDebitNoteService.submit_debit_note(
                    debit_note_id=debit_note_id,
                    tenant=tenant,
                    submitted_by=person
                )
                messages.success(request, f'Debit note {debit_note.debit_note_number} submitted for approval.')
            
            elif action == 'approve':
                debit_note = SupplierDebitNoteService.approve_debit_note(
                    debit_note_id=debit_note_id,
                    tenant=tenant,
                    approved_by=person
                )
                messages.success(request, f'Debit note {debit_note.debit_note_number} approved successfully.')
            
            elif action == 'reject':
                rejection_reason = request.POST.get('rejection_reason')
                debit_note = SupplierDebitNoteService.reject_debit_note(
                    debit_note_id=debit_note_id,
                    tenant=tenant,
                    rejected_by=person,
                    rejection_reason=rejection_reason
                )
                messages.warning(request, f'Debit note {debit_note.debit_note_number} rejected.')
            
            elif action == 'cancel':
                debit_note = SupplierDebitNoteService.cancel_debit_note(
                    debit_note_id=debit_note_id,
                    tenant=tenant,
                    cancelled_by=person
                )
                messages.info(request, f'Debit note {debit_note.debit_note_number} cancelled.')
            
            return redirect('supplier_debit_note_detail', debit_note_id=debit_note_id)
        
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
            return redirect('supplier_debit_note_detail', debit_note_id=debit_note_id)


class SupplierDebitNoteUpdateWebView(View):
    """
    Update Supplier Debit Note View (for draft notes only).
    """
    def get(self, request, debit_note_id):
        if not request.user.is_authenticated:
            return redirect('login_web')

        tenant = getattr(request, 'tenant', None)
        from backend.apps.efbm.services.payables import SupplierDebitNoteService
        
        try:
            debit_note = SupplierDebitNoteService.get_debit_note(debit_note_id, tenant)
            
            if debit_note.status != 'draft':
                from django.contrib import messages
                messages.error(request, 'Only draft debit notes can be updated.')
                return redirect('supplier_debit_note_detail', debit_note_id=debit_note_id)
            
            from backend.apps.efbm.models import SupplierBill
            bills = SupplierBill.objects.filter(tenant=tenant, status__in=['pending', 'approved', 'partial'])
            
            context = {
                'debit_note': debit_note,
                'bills': bills
            }
            return render(request, 'efbm/payables/supplier_debit_note_form.html', context)
        except Exception as e:
            from django.contrib import messages
            messages.error(request, f'Debit note not found: {str(e)}')
            return redirect('supplier_debit_notes')
    
    def post(self, request, debit_note_id):
        if not request.user.is_authenticated:
            return redirect('login_web')

        tenant = getattr(request, 'tenant', None)
        amount = request.POST.get('amount')
        reason = request.POST.get('reason')
        description = request.POST.get('description')
        
        from backend.apps.efbm.services.payables import SupplierDebitNoteService
        from django.contrib import messages
        
        try:
            from backend.apps.people.models import Person
            updated_by = Person.objects.filter(user=request.user, tenant=tenant).first()
            
            debit_note = SupplierDebitNoteService.update_debit_note(
                debit_note_id=debit_note_id,
                tenant=tenant,
                amount=amount,
                reason=reason,
                description=description,
                updated_by=updated_by
            )
            messages.success(request, f'Debit note {debit_note.debit_note_number} updated successfully.')
            return redirect('supplier_debit_note_detail', debit_note_id=debit_note.id)
        except Exception as e:
            messages.error(request, f'Error updating debit note: {str(e)}')
            return redirect('supplier_debit_note_update', debit_note_id=debit_note_id)



class SupplierCreditNoteUpdateWebView(View):
    """
    Update Draft Supplier Credit Note View.
    """
    def get(self, request, credit_note_id):
        if not request.user.is_authenticated:
            return redirect('login_web')

        tenant = getattr(request, 'tenant', None)
        from backend.apps.efbm.services.supplier_credit_notes import SupplierCreditNoteService
        
        try:
            credit_note = SupplierCreditNoteService.get_credit_note(credit_note_id, tenant)
            
            if credit_note.status != 'draft':
                from django.contrib import messages
                messages.error(request, 'Only draft credit notes can be edited.')
                return redirect('supplier_credit_note_detail', credit_note_id=credit_note_id)
            
            context = {'credit_note': credit_note}
            return render(request, 'efbm/payables/supplier_credit_note_form.html', context)
        except Exception as e:
            from django.contrib import messages
            messages.error(request, f'Credit note not found: {str(e)}')
            return redirect('supplier_credit_notes')
    
    def post(self, request, credit_note_id):
        if not request.user.is_authenticated:
            return redirect('login_web')

        tenant = getattr(request, 'tenant', None)
        amount = request.POST.get('amount')
        reason = request.POST.get('reason')
        
        from backend.apps.efbm.services.supplier_credit_notes import SupplierCreditNoteService
        from django.contrib import messages
        
        try:
            from backend.apps.people.models import Person
            updated_by = Person.objects.filter(user=request.user, tenant=tenant).first()
            
            credit_note = SupplierCreditNoteService.update_credit_note(
                credit_note_id=credit_note_id,
                tenant=tenant,
                amount=amount,
                reason=reason,
                updated_by=updated_by
            )
            messages.success(request, f'Credit note {credit_note.note_number} updated successfully.')
            return redirect('supplier_credit_note_detail', credit_note_id=credit_note.id)
        except Exception as e:
            messages.error(request, f'Error updating credit note: {str(e)}')
            return redirect('supplier_credit_note_edit', credit_note_id=credit_note_id)


# ==============================================================
# PHASE 8: SUPPLIER PAYMENT & PAYMENT VOUCHER VIEWS
# ==============================================================

class SupplierPaymentListView(View):
    """
    Supplier Payments List & Management View.
    """
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        tenant = getattr(request, 'tenant', None)
        status_filter = request.GET.get('status')
        bill_id = request.GET.get('bill_id')
        
        from backend.apps.efbm.models import SupplierPayment
        payments = SupplierPayment.objects.filter(tenant=tenant).select_related(
            'bill', 'prepared_by', 'approved_by', 'processed_by', 'bank_account'
        ).prefetch_related('voucher')
        
        if status_filter:
            payments = payments.filter(status=status_filter)
        
        if bill_id:
            payments = payments.filter(bill_id=bill_id)
        
        payments = payments.order_by('-payment_date', '-created_at')
        
        context = {
            'payments': payments,
            'status_filter': status_filter,
            'status_choices': SupplierPayment.STATUS_CHOICES
        }
        return render(request, 'efbm/payments/supplier_payments.html', context)


class SupplierPaymentCreateView(View):
    """
    Create Supplier Payment View.
    """
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        tenant = getattr(request, 'tenant', None)
        bill_id = request.GET.get('bill_id')
        
        from backend.apps.efbm.models import SupplierBill, BankAccount
        bills = SupplierBill.objects.filter(tenant=tenant, status__in=['approved', 'partial']).select_related()
        bank_accounts = BankAccount.objects.filter(tenant=tenant)
        selected_bill = bills.filter(id=bill_id).first() if bill_id else None
        
        context = {
            'bills': bills,
            'bank_accounts': bank_accounts,
            'selected_bill': selected_bill
        }
        return render(request, 'efbm/payments/supplier_payment_form.html', context)
    
    def post(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        tenant = getattr(request, 'tenant', None)
        bill_id = request.POST.get('bill_id')
        amount = request.POST.get('amount')
        payment_method = request.POST.get('payment_method', 'bank_transfer')
        bank_account_id = request.POST.get('bank_account_id')
        description = request.POST.get('description', '')
        withholding_tax_rate = request.POST.get('withholding_tax_rate')
        
        from backend.apps.efbm.services.payables import SupplierPaymentService
        from django.contrib import messages
        
        try:
            from backend.apps.people.models import Person
            prepared_by = Person.objects.filter(user=request.user, tenant=tenant).first()
            
            payment = SupplierPaymentService.create_payment(
                tenant=tenant,
                bill_id=bill_id,
                amount=amount,
                payment_method=payment_method,
                bank_account_id=bank_account_id,
                description=description,
                withholding_tax_rate=withholding_tax_rate,
                prepared_by=prepared_by
            )
            messages.success(request, f'Payment {payment.payment_number} created successfully.')
            return redirect('supplier_payment_detail', payment_id=payment.id)
        except Exception as e:
            messages.error(request, f'Error creating payment: {str(e)}')
            return redirect('supplier_payment_create')


class SupplierPaymentDetailView(View):
    """
    Supplier Payment Detail & Actions View.
    """
    def get(self, request, payment_id):
        if not request.user.is_authenticated:
            return redirect('login_web')

        tenant = getattr(request, 'tenant', None)
        from backend.apps.efbm.models import SupplierPayment
        
        try:
            payment = SupplierPayment.objects.select_related(
                'bill', 'prepared_by', 'approved_by', 'processed_by', 'bank_account'
            ).get(id=payment_id, tenant=tenant)
            
            context = {'payment': payment}
            return render(request, 'efbm/payments/supplier_payment_detail.html', context)
        except SupplierPayment.DoesNotExist:
            from django.contrib import messages
            messages.error(request, 'Payment not found.')
            return redirect('supplier_payments')
    
    def post(self, request, payment_id):
        if not request.user.is_authenticated:
            return redirect('login_web')

        tenant = getattr(request, 'tenant', None)
        action = request.POST.get('action')
        
        from backend.apps.efbm.services.payables import SupplierPaymentService
        from backend.apps.people.models import Person
        from django.contrib import messages
        
        try:
            person = Person.objects.filter(user=request.user, tenant=tenant).first()
            
            if action == 'submit':
                payment = SupplierPaymentService.submit_payment_for_approval(
                    payment_id=payment_id,
                    tenant=tenant,
                    submitted_by=person
                )
                messages.success(request, f'Payment {payment.payment_number} submitted for approval.')
            
            elif action == 'approve':
                result = SupplierPaymentService.approve_payment(
                    payment_id=payment_id,
                    tenant=tenant,
                    approved_by=person
                )
                payment = result['payment']
                voucher = result['voucher']
                messages.success(request, f'Payment {payment.payment_number} approved and voucher {voucher.voucher_number} created.')
            
            elif action == 'process':
                bank_reference = request.POST.get('bank_reference', '')
                payment = SupplierPaymentService.process_payment(
                    payment_id=payment_id,
                    tenant=tenant,
                    processed_by=person,
                    bank_reference=bank_reference
                )
                messages.success(request, f'Payment {payment.payment_number} processed successfully.')
            
            return redirect('supplier_payment_detail', payment_id=payment_id)
        
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
            return redirect('supplier_payment_detail', payment_id=payment_id)


class SupplierPaymentUpdateView(View):
    """
    Update Supplier Payment View (for draft payments only).
    """
    def get(self, request, payment_id):
        if not request.user.is_authenticated:
            return redirect('login_web')

        tenant = getattr(request, 'tenant', None)
        from backend.apps.efbm.models import SupplierPayment, BankAccount
        
        try:
            payment = SupplierPayment.objects.select_related('bill', 'bank_account').get(id=payment_id, tenant=tenant)
            
            if payment.status != 'draft':
                from django.contrib import messages
                messages.error(request, 'Only draft payments can be updated.')
                return redirect('supplier_payment_detail', payment_id=payment_id)
            
            bank_accounts = BankAccount.objects.filter(tenant=tenant)
            
            context = {
                'payment': payment,
                'bank_accounts': bank_accounts
            }
            return render(request, 'efbm/payments/supplier_payment_form.html', context)
        except SupplierPayment.DoesNotExist:
            from django.contrib import messages
            messages.error(request, 'Payment not found.')
            return redirect('supplier_payments')
    
    def post(self, request, payment_id):
        if not request.user.is_authenticated:
            return redirect('login_web')

        tenant = getattr(request, 'tenant', None)
        amount = request.POST.get('amount')
        payment_method = request.POST.get('payment_method')
        bank_account_id = request.POST.get('bank_account_id')
        description = request.POST.get('description')
        withholding_tax_rate = request.POST.get('withholding_tax_rate')
        
        from backend.apps.efbm.services.payables import SupplierPaymentService
        from django.contrib import messages
        
        try:
            from backend.apps.people.models import Person
            updated_by = Person.objects.filter(user=request.user, tenant=tenant).first()
            
            payment = SupplierPaymentService.update_payment(
                payment_id=payment_id,
                tenant=tenant,
                amount=amount,
                payment_method=payment_method,
                bank_account_id=bank_account_id,
                description=description,
                withholding_tax_rate=withholding_tax_rate,
                updated_by=updated_by
            )
            messages.success(request, f'Payment {payment.payment_number} updated successfully.')
            return redirect('supplier_payment_detail', payment_id=payment.id)
        except Exception as e:
            messages.error(request, f'Error updating payment: {str(e)}')
            return redirect('supplier_payment_update', payment_id=payment_id)


class PaymentVoucherListView(View):
    """
    Payment Vouchers List & Management View.
    """
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        tenant = getattr(request, 'tenant', None)
        status_filter = request.GET.get('status')
        
        from backend.apps.efbm.models import PaymentVoucher
        vouchers = PaymentVoucher.objects.filter(tenant=tenant).select_related(
            'payment__bill', 'prepared_by', 'approved_by', 'processed_by'
        )
        
        if status_filter:
            vouchers = vouchers.filter(status=status_filter)
        
        vouchers = vouchers.order_by('-created_at')
        
        context = {
            'vouchers': vouchers,
            'status_filter': status_filter,
            'status_choices': PaymentVoucher.STATUS_CHOICES
        }
        return render(request, 'efbm/payments/payment_vouchers.html', context)


class PaymentVoucherDetailView(View):
    """
    Payment Voucher Detail View.
    """
    def get(self, request, voucher_id):
        if not request.user.is_authenticated:
            return redirect('login_web')

        tenant = getattr(request, 'tenant', None)
        from backend.apps.efbm.models import PaymentVoucher
        
        try:
            voucher = PaymentVoucher.objects.select_related(
                'payment__bill', 'prepared_by', 'approved_by', 'processed_by'
            ).get(id=voucher_id, tenant=tenant)
            
            context = {'voucher': voucher}
            return render(request, 'efbm/payments/payment_voucher_detail.html', context)
        except PaymentVoucher.DoesNotExist:
            from django.contrib import messages
            messages.error(request, 'Payment voucher not found.')
            return redirect('payment_vouchers')
