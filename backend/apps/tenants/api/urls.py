from django.urls import path
from backend.apps.tenants.api.views import (
    SubscriptionPlanListAPIView, SubscriptionSubscribeAPIView, SubscriptionRenewAPIView,
    SubscriptionStatusAPIView, OPayWebhookAPIView, PaystackWebhookAPIView
)

app_name = 'tenants_api'

urlpatterns = [
    path('subscription/plans/', SubscriptionPlanListAPIView.as_view(), name='subscription_plans'),
    path('subscription/subscribe/', SubscriptionSubscribeAPIView.as_view(), name='subscription_subscribe'),
    path('subscription/renew/', SubscriptionRenewAPIView.as_view(), name='subscription_renew'),
    path('subscription/status/', SubscriptionStatusAPIView.as_view(), name='subscription_status'),
    path('subscription/webhook/opay/', OPayWebhookAPIView.as_view(), name='opay_webhook'),
    path('subscription/webhook/paystack/', PaystackWebhookAPIView.as_view(), name='paystack_webhook'),
]
