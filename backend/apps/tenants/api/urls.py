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
from backend.apps.tenants.api.views_mobile import (
    MobileConfigAPIView, MobileJWTLoginAPIView, MobileLogoutAPIView,
    SingleRequestRoleDashboardAPIView, MobileFeeCalculationAPIView,
    MobilePaymentInitializeAPIView, MobileInvoicePDFStreamAPIView,
    MobileReceiptPDFStreamAPIView, MobileNotificationsAPIView, MobileDeltaSyncAPIView
)

app_name = 'tenants_api'

urlpatterns = [
    # Mobile Startup Config & Auth
    path('mobile/config/', MobileConfigAPIView.as_view(), name='mobile_config'),
    path('auth/token/', MobileJWTLoginAPIView.as_view(), name='jwt_login'),
    path('auth/logout/', MobileLogoutAPIView.as_view(), name='jwt_logout'),

    # Role Aggregated Mobile Dashboards
    path('dashboards/<str:role>/', SingleRequestRoleDashboardAPIView.as_view(), name='mobile_role_dashboard'),

    # Mobile Billing & Payment APIs
    path('mobile-billing/fee-calculation/', MobileFeeCalculationAPIView.as_view(), name='mobile_fee_calculation'),
    path('mobile-billing/initialize-payment/', MobilePaymentInitializeAPIView.as_view(), name='mobile_payment_initialize'),

    # Media & PDF Downloads
    path('media/invoices/<uuid:invoice_id>/pdf/', MobileInvoicePDFStreamAPIView.as_view(), name='mobile_invoice_pdf'),
    path('media/receipts/<uuid:payment_id>/pdf/', MobileReceiptPDFStreamAPIView.as_view(), name='mobile_receipt_pdf'),

    # Push Notifications & Sync
    path('mobile/notifications/', MobileNotificationsAPIView.as_view(), name='mobile_notifications'),
    path('sync/delta/', MobileDeltaSyncAPIView.as_view(), name='mobile_delta_sync'),

    # Legacy subscription & payment endpoints
    path('subscription/plans/', SubscriptionPlanListAPIView.as_view(), name='subscription_plans'),
    path('subscription/subscribe/', SubscriptionSubscribeAPIView.as_view(), name='subscription_subscribe'),
    path('subscription/renew/', SubscriptionRenewAPIView.as_view(), name='subscription_renew'),
    path('subscription/status/', SubscriptionStatusAPIView.as_view(), name='subscription_status'),
    path('subscription/webhook/opay/', OPayWebhookAPIView.as_view(), name='opay_webhook_legacy'),
    path('subscription/webhook/paystack/', PaystackWebhookAPIView.as_view(), name='paystack_webhook_legacy'),

    path('billing/payment/initialize/', PaymentInitializeAPIView.as_view(), name='payment_initialize'),
    path('billing/payment/verify/', PaymentVerifyAPIView.as_view(), name='payment_verify'),
    path('billing/payment/webhook/paystack/', PaystackWebhookAPIView.as_view(), name='paystack_webhook'),
    path('billing/payment/webhook/opay/', OPayWebhookAPIView.as_view(), name='opay_webhook'),
    path('billing/manual-payment/', ManualPaymentAPIView.as_view(), name='manual_payment'),
    path('billing/payment-status/', PaymentStatusAPIView.as_view(), name='payment_status'),
]
