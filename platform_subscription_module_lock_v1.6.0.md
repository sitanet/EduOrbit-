# EduOrbit ERP v1.6.0 — Platform Subscription & Billing Engine Specification

> **Module Status**: `FROZEN & LOCKED (v1.6.0-PLATFORM-BILLING)`  
> **Release Tag**: `v1.6.0-PLATFORM-BILLING`  
> **Target Date**: July 27, 2026  
> **Scope**: Multi-Model Billing (`SCHOOL_PAY`, `PARENT_PAY`, `HYBRID`), Flexible Cycles (`MONTHLY`, `TERMLY`, `YEARLY`), OPay & Paystack Payment Gateway Abstraction, Grace Periods, & Reusable Subscription Enforcement Engine.

---

## 1. Executive Summary & Architecture Overview

The **Platform Subscription & SaaS Billing Engine Enhancement** of **EduOrbit ERP v1.6.0** has been updated to support dual payment provider options (**OPay** and **Paystack**), verified, tested, and locked under tag `v1.6.0-PLATFORM-BILLING`.

This platform-level engine operates independently from student fee collection and manages EduOrbit's corporate SaaS revenue streams.

---

## 2. Implemented & Verified Components

1. **Subscription & Billing Models** (`backend/apps/tenants/models.py`):
   - `SubscriptionPlan`: Enhanced to support `SCHOOL_PAY`, `PARENT_PAY`, and `HYBRID` models with independent `monthly_price`, `termly_price`, `yearly_price`, `trial_days`, `grace_period_days`, `max_students`, and `max_staff` controls.
   - `TenantSubscription`: Upgraded to manage tenant licenses, status lifecycle (`TRIAL`, `ACTIVE`, `GRACE`, `EXPIRED`, `SUSPENDED`, `CANCELLED`), auto-renewals, renewal history, and `payment_provider` selection (`OPay`, `Paystack`).
   - `StudentPlatformSubscription`: Models direct parent platform subscriptions under `PARENT_PAY` and `HYBRID` models.
2. **Payment Gateway Abstraction & Dual Providers** (`backend/apps/tenants/services/gateways.py`):
   - `PaymentGateway`: Abstract provider interface (`charge`, `verify`, `handle_webhook`).
   - `OPayGateway`: Implements OPay card payments, wallet checkout, payment verification, and webhook handling.
   - `PaystackGateway`: Implements Paystack card payments, bank transfers, USSD checkout, payment verification, and webhook handling (`charge.success`).
   - `get_payment_gateway()`: Factory helper instantiating the tenant's chosen payment provider.
3. **Subscription Enforcement Engine** (`backend/apps/tenants/services/subscription.py`):
   - `SubscriptionService.create_tenant_subscription()` & `renew_subscription()`.
   - `SubscriptionValidationService.validate_tenant_access()` & `validate_limits()` (Reusable across all EduOrbit modules to enforce subscription status, grace periods, module access, and capacity limits).
4. **REST APIs & URLs** (`backend/apps/tenants/api/views.py` & `urls.py`):
   - `GET /tenants/api/v1/subscription/plans/` -> `SubscriptionPlanListAPIView`
   - `POST /tenants/api/v1/subscription/subscribe/` -> `SubscriptionSubscribeAPIView`
   - `POST /tenants/api/v1/subscription/renew/` -> `SubscriptionRenewAPIView`
   - `GET /tenants/api/v1/subscription/status/` -> `SubscriptionStatusAPIView`
   - `POST /tenants/api/v1/subscription/webhook/opay/` -> `OPayWebhookAPIView`
   - `POST /tenants/api/v1/subscription/webhook/paystack/` -> `PaystackWebhookAPIView`

---

## 3. Automated Test Verification Results

Executing `scratch/run_platform_billing_test.py` verified 100% test pass rate:
```bash
=== Running Platform Subscription & Billing Engine Master Test Battery ===
PASSED: test_subscription_creation_and_validation
PASSED: test_opay_and_paystack_gateways_and_renewal
PASSED: test_platform_subscription_api_endpoints

=== ALL PLATFORM BILLING TESTS PASSED SUCCESSFULLY! ===
```
- **System Check Output**: `python manage.py check` -> `System check identified no issues (0 silenced).`
- **Git Tag Created**: **`v1.6.0-PLATFORM-BILLING`**
