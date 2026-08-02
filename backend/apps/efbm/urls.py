from django.urls import path, include
from django.views.generic import RedirectView
from backend.apps.efbm.views_web import (
    EFBMDashboardWebView, ParentWalletWebView, TrialBalanceWebView,
    BalanceSheetWebView, IncomeStatementWebView, CashFlowWebView,
    GeneralLedgerWebView, AccountStatementWebView, JournalReportWebView,
    ChartOfAccountsWebView, ReceivablesDashboardWebView, OutstandingInvoicesWebView,
    InvoiceAgingWebView, PaymentHistoryWebView, PayablesDashboardWebView,
    SupplierBillsWebView, VendorAgingWebView, BankDashboardWebView,
    BankReconciliationWebView, ChequeRegisterWebView, CashbookWebView,
    BudgetDashboardWebView, BudgetVsActualWebView, ExecutiveAnalyticsWebView,
    CustomerLedgerWebView, CreditNoteWebView, DebitNoteWebView,
    BadDebtWriteOffWebView, BalanceConfirmationWebView, SupplierCreditNotesWebView,
    SupplierCreditNoteListWebView, SupplierCreditNoteCreateWebView,
    SupplierCreditNoteDetailWebView, SupplierCreditNoteUpdateWebView,
    SupplierDebitNoteListWebView, SupplierDebitNoteCreateWebView,
    SupplierDebitNoteDetailWebView, SupplierDebitNoteUpdateWebView,
    SupplierPaymentListView, SupplierPaymentCreateView, SupplierPaymentDetailView,
    SupplierPaymentUpdateView, PaymentVoucherListView, PaymentVoucherDetailView
)

urlpatterns = [
    # Root redirect to dashboard
    path('', RedirectView.as_view(url='dashboard/', permanent=False)),
    # Web views
    path('dashboard/', EFBMDashboardWebView.as_view(), name='efbm_dashboard_web'),
    path('wallet-portal/', ParentWalletWebView.as_view(), name='wallet_portal_web'),
    path('trial-balance/', TrialBalanceWebView.as_view(), name='trial_balance_web'),
    path('balance-sheet/', BalanceSheetWebView.as_view(), name='balance_sheet_web'),
    path('income-statement/', IncomeStatementWebView.as_view(), name='income_statement_web'),
    path('cash-flow/', CashFlowWebView.as_view(), name='cash_flow_web'),
    path('general-ledger/', GeneralLedgerWebView.as_view(), name='general_ledger_web'),
    path('account-statement/', AccountStatementWebView.as_view(), name='account_statement_web'),
    path('journals/', JournalReportWebView.as_view(), name='journal_report_web'),
    path('chart-of-accounts/', ChartOfAccountsWebView.as_view(), name='chart_of_accounts_web'),
    
    # Accounts Receivable routes
    path('receivables/', ReceivablesDashboardWebView.as_view(), name='receivables_dashboard_web'),
    path('receivables/outstanding/', OutstandingInvoicesWebView.as_view(), name='outstanding_invoices_web'),
    path('receivables/aging/', InvoiceAgingWebView.as_view(), name='invoice_aging_web'),
    path('receivables/payments/', PaymentHistoryWebView.as_view(), name='payment_history_web'),
    path('receivables/ledger/', CustomerLedgerWebView.as_view(), name='customer_ledger_web'),
    path('receivables/credit-notes/', CreditNoteWebView.as_view(), name='credit_notes_web'),
    path('receivables/debit-notes/', DebitNoteWebView.as_view(), name='debit_notes_web'),
    path('receivables/bad-debts/', BadDebtWriteOffWebView.as_view(), name='bad_debts_web'),
    path('receivables/balance-confirmations/', BalanceConfirmationWebView.as_view(), name='balance_confirmations_web'),

    # Accounts Payable routes
    path('payables/', PayablesDashboardWebView.as_view(), name='payables_dashboard_web'),
    path('payables/bills/', SupplierBillsWebView.as_view(), name='supplier_bills_web'),
    path('payables/aging/', VendorAgingWebView.as_view(), name='vendor_aging_web'),
    path('payables/credit-notes/', SupplierCreditNoteListWebView.as_view(), name='supplier_credit_notes'),
    path('payables/credit-notes/create/', SupplierCreditNoteCreateWebView.as_view(), name='supplier_credit_note_create'),
    path('payables/credit-notes/<uuid:credit_note_id>/', SupplierCreditNoteDetailWebView.as_view(), name='supplier_credit_note_detail'),
    path('payables/credit-notes/<uuid:credit_note_id>/edit/', SupplierCreditNoteUpdateWebView.as_view(), name='supplier_credit_note_edit'),
    path('payables/debit-notes/', SupplierDebitNoteListWebView.as_view(), name='supplier_debit_notes'),
    path('payables/debit-notes/create/', SupplierDebitNoteCreateWebView.as_view(), name='supplier_debit_note_create'),
    path('payables/debit-notes/<uuid:debit_note_id>/', SupplierDebitNoteDetailWebView.as_view(), name='supplier_debit_note_detail'),
    path('payables/debit-notes/<uuid:debit_note_id>/edit/', SupplierDebitNoteUpdateWebView.as_view(), name='supplier_debit_note_update'),
    
    # Supplier Payment & Voucher Routes (Phase 8)
    path('payables/payments/', SupplierPaymentListView.as_view(), name='supplier_payments'),
    path('payables/payments/create/', SupplierPaymentCreateView.as_view(), name='supplier_payment_create'),
    path('payables/payments/<uuid:payment_id>/', SupplierPaymentDetailView.as_view(), name='supplier_payment_detail'),
    path('payables/payments/<uuid:payment_id>/edit/', SupplierPaymentUpdateView.as_view(), name='supplier_payment_update'),
    path('payables/vouchers/', PaymentVoucherListView.as_view(), name='payment_vouchers'),
    path('payables/vouchers/<uuid:voucher_id>/', PaymentVoucherDetailView.as_view(), name='payment_voucher_detail'),


    # Bank & Treasury Management routes
    path('banking/', BankDashboardWebView.as_view(), name='bank_dashboard_web'),
    path('banking/reconciliation/', BankReconciliationWebView.as_view(), name='bank_reconciliation_web'),
    path('banking/cheques/', ChequeRegisterWebView.as_view(), name='cheque_register_web'),
    path('banking/cashbook/', CashbookWebView.as_view(), name='cashbook_web'),

    # Enterprise Budgeting routes
    path('budgeting/', BudgetDashboardWebView.as_view(), name='budget_dashboard_web'),
    path('budgeting/vs-actual/', BudgetVsActualWebView.as_view(), name='budget_vs_actual_web'),

    # Executive Financial Analytics route
    path('analytics/', ExecutiveAnalyticsWebView.as_view(), name='executive_analytics_web'),

    # ── Top-level shortcut aliases (prevent 404 on common direct URLs) ────
    path('payments/',   PaymentHistoryWebView.as_view(),       name='efbm_payments_alias'),
    path('invoices/',   OutstandingInvoicesWebView.as_view(),  name='efbm_invoices_alias'),
    path('budget/',     BudgetDashboardWebView.as_view(),      name='efbm_budget_alias'),
    path('banking/',    BankDashboardWebView.as_view(),        name='efbm_banking_alias'),
    path('reports/',    ExecutiveAnalyticsWebView.as_view(),   name='efbm_reports_alias'),

    # API endpoints versions
    path('api/v1/', include('backend.apps.efbm.api.urls')),
]
