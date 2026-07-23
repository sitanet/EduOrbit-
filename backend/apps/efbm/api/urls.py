from django.urls import path
from backend.apps.efbm.api.views import (
    InvoiceAPIView, PaymentAPIView, WalletAPIView
)

app_name = 'efbm_api'

urlpatterns = [
    path('invoices/', InvoiceAPIView.as_view(), name='invoices'),
    path('payments/', PaymentAPIView.as_view(), name='payments'),
    path('wallet/', WalletAPIView.as_view(), name='wallet'),
]
