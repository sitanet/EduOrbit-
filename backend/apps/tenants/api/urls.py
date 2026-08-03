from django.urls import path
from backend.apps.tenants.api.views import (
    SubscriptionPlanListAPIView, SubscriptionSubscribeAPIView, SubscriptionRenewAPIView,
    SubscriptionStatusAPIView
)
from backend.apps.tenants.api.views_payment import (
    PaymentInitializeAPIView, PaymentVerifyAPIView,
    PaystackWebhookAPIView, OPayWebhookAPIView,
    ManualPaymentAPIView, PaymentStatusAPIView
)

app_name = 'tenants_api'

urlpatterns = [
    # Legacy subscription endpoints
    path('subscription/plans/', SubscriptionPlanListAPIView.as_view(), name='subscription_plans'),
    path('subscription/subscribe/', SubscriptionSubscribeAPIView.as_view(), name='subscription_subscribe'),
    path('subscription/renew/', SubscriptionRenewAPIView.as_view(), name='subscription_renew'),
    path('subscription/status/', SubscriptionStatusAPIView.as_view(), name='subscription_status'),

    # Phase 3 Multi-Gateway Payment System Endpoints
    path('billing/payment/initialize/', PaymentInitializeAPIView.as_view(), name='payment_initialize'),
    path('billing/payment/verify/', PaymentVerifyAPIView.as_view(), name='payment_verify'),
    path('billing/payment/webhook/paystack/', PaystackWebhookAPIView.as_view(), name='paystack_webhook'),
    path('billing/payment/webhook/opay/', OPayWebhookAPIView.as_view(), name='opay_webhook'),
    path('billing/manual-payment/', ManualPaymentAPIView.as_view(), name='manual_payment'),
    path('billing/payment-status/', PaymentStatusAPIView.as_view(), name='payment_status'),
]
