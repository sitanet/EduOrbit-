from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from backend.apps.tenants.models import SubscriptionPlan, TenantSubscription, StudentPlatformSubscription
from backend.apps.tenants.services.gateways import OPayGateway
from backend.apps.core.services.notifications import UnifiedNotificationService

class SubscriptionService:
    """
    Platform Subscription Provisioning & Renewal Engine.
    """
    @classmethod
    @transaction.atomic
    def create_tenant_subscription(cls, tenant, plan, billing_cycle='MONTHLY', billing_model='SCHOOL_PAY'):
        duration_days = 30 if billing_cycle == 'MONTHLY' else (120 if billing_cycle == 'TERMLY' else 365)
        start_date = timezone.now()
        end_date = start_date + timezone.timedelta(days=duration_days)
        grace_ends = end_date + timezone.timedelta(days=plan.grace_period_days)

        subscription, _ = TenantSubscription.objects.get_or_create(
            tenant=tenant,
            defaults={
                'plan': plan,
                'billing_model': billing_model,
                'billing_cycle': billing_cycle,
                'status': 'ACTIVE',
                'start_date': start_date,
                'end_date': end_date,
                'grace_period_ends_at': grace_ends
            }
        )

        subscription.plan = plan
        subscription.billing_model = billing_model
        subscription.billing_cycle = billing_cycle
        subscription.status = 'ACTIVE'
        subscription.end_date = end_date
        subscription.grace_period_ends_at = grace_ends
        subscription.save()

        UnifiedNotificationService.send_notification(
            recipient=tenant.name,
            title="Subscription Activated",
            message=f"Platform Subscription for {plan.name} ({billing_model} / {billing_cycle}) is now ACTIVE.",
            channels=['in_app', 'email']
        )

        return {
            "status": "success",
            "subscription_id": str(subscription.id),
            "tenant_name": tenant.name,
            "plan_name": plan.name,
            "billing_model": billing_model,
            "billing_cycle": billing_cycle,
            "end_date": str(end_date)
        }

    @classmethod
    @transaction.atomic
    def renew_subscription(cls, subscription, payment_reference):
        # Verify Payment with Gateway (OPay, Paystack, etc.)
        from backend.apps.tenants.services.gateways import get_payment_gateway
        gateway = get_payment_gateway(subscription.payment_provider)
        verification = gateway.verify(reference=payment_reference)

        if not verification.get('verified'):
            return {"status": "error", "message": "Payment verification failed."}

        plan = subscription.plan
        duration_days = 30 if subscription.billing_cycle == 'MONTHLY' else (120 if subscription.billing_cycle == 'TERMLY' else 365)

        subscription.start_date = timezone.now()
        subscription.end_date = timezone.now() + timezone.timedelta(days=duration_days)
        subscription.grace_period_ends_at = subscription.end_date + timezone.timedelta(days=plan.grace_period_days if plan else 7)
        subscription.status = 'ACTIVE'
        
        # Log Renewal
        history = subscription.renewal_history or []
        history.append({
            "renewed_at": str(timezone.now()),
            "payment_reference": payment_reference,
            "amount": float(plan.monthly_price if plan else 0.0)
        })
        subscription.renewal_history = history
        subscription.save()

        return {
            "status": "success",
            "subscription_id": str(subscription.id),
            "payment_reference": payment_reference,
            "new_end_date": str(subscription.end_date)
        }


class SubscriptionValidationService:
    """
    Platform Subscription Enforcement & Feature Toggle Engine.
    Reusable by all EduOrbit modules.
    """
    @classmethod
    def validate_tenant_access(cls, tenant, module_name=None):
        try:
            sub = TenantSubscription.objects.get(tenant=tenant)
            now = timezone.now()

            if sub.status in ['SUSPENDED', 'CANCELLED']:
                return {"is_valid": False, "reason": f"Subscription is {sub.status}."}

            if sub.end_date < now and (not sub.grace_period_ends_at or sub.grace_period_ends_at < now):
                return {"is_valid": False, "reason": "Subscription EXPIRED past grace period."}

            if module_name and sub.plan:
                if module_name == 'lms' and not sub.plan.lms_enabled:
                    return {"is_valid": False, "reason": "LMS Module not enabled in subscription plan."}
                if module_name == 'cbt' and not sub.plan.cbt_enabled:
                    return {"is_valid": False, "reason": "CBT Module not enabled in subscription plan."}

            is_grace = sub.end_date < now <= sub.grace_period_ends_at if sub.grace_period_ends_at else False

            return {
                "is_valid": True,
                "status": "GRACE" if is_grace else sub.status,
                "plan_name": sub.plan.name if sub.plan else "Custom",
                "billing_model": sub.billing_model
            }

        except TenantSubscription.DoesNotExist:
            return {"is_valid": False, "reason": "No active tenant subscription found."}

    @classmethod
    def validate_limits(cls, tenant, current_students=0, current_staff=0):
        try:
            sub = TenantSubscription.objects.get(tenant=tenant)
            plan = sub.plan
            if not plan:
                return {"within_limits": True}

            if current_students > plan.max_students:
                return {
                    "within_limits": False,
                    "reason": f"Student limit exceeded. Limit: {plan.max_students}, Current: {current_students}"
                }

            if current_staff > plan.max_staff:
                return {
                    "within_limits": False,
                    "reason": f"Staff limit exceeded. Limit: {plan.max_staff}, Current: {current_staff}"
                }

            return {"within_limits": True}
        except TenantSubscription.DoesNotExist:
            return {"within_limits": False, "reason": "No subscription plan configured."}
