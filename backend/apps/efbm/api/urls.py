from django.urls import path
from backend.apps.efbm.api.views import (
    InvoiceGenerateAPIView, InvoiceListAPIView, PaymentCreateAPIView, WalletDetailAPIView, WalletFundAPIView,
    JournalPostAPIView, TrialBalanceAPIView, ProfitLossAPIView, BalanceSheetAPIView,
    BudgetCreateAPIView, BudgetApproveAPIView, BudgetUtilizationAPIView, BudgetVarianceAPIView
)

app_name = 'finance_api'

urlpatterns = [
    path('invoices/generate/', InvoiceGenerateAPIView.as_view(), name='invoice_generate'),
    path('invoices/', InvoiceListAPIView.as_view(), name='invoice_list'),
    path('payments/', PaymentCreateAPIView.as_view(), name='payment_create'),
    path('wallet/', WalletDetailAPIView.as_view(), name='wallet_detail'),
    path('wallet/fund/', WalletFundAPIView.as_view(), name='wallet_fund'),
    path('journals/post/', JournalPostAPIView.as_view(), name='journal_post'),
    path('trial-balance/', TrialBalanceAPIView.as_view(), name='trial_balance'),
    path('profit-loss/', ProfitLossAPIView.as_view(), name='profit_loss'),
    path('balance-sheet/', BalanceSheetAPIView.as_view(), name='balance_sheet'),
    path('budgets/', BudgetCreateAPIView.as_view(), name='budget_create'),
    path('budgets/approve/', BudgetApproveAPIView.as_view(), name='budget_approve'),
    path('budget-utilization/', BudgetUtilizationAPIView.as_view(), name='budget_utilization'),
    path('budget-variance/', BudgetVarianceAPIView.as_view(), name='budget_variance'),
]
