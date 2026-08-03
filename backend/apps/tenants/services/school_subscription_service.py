"""
School Subscription Service for EduOrbit SaaS Platform.
Manages TenantSubscription provisioning, tier calculations, and platform-wide Parent/Student access activation.
"""

import logging
from decimal import Decimal
from typing import Optional
from django.db import transaction
from django.utils import timezone

from backend.apps.tenants.dto import ServiceResult
from backend.apps.tenants.exceptions import SubscriptionException
from backend.apps.tenants.models import Tenant, SubscriptionPlan, TenantSubscription
from backend.apps.tenants.services.billing_calculator import BillingCalculationService
from backend.apps.people.models import StudentProfile

logger = logging.getLogger(__name__)


class SchoolSubscriptionService:
    """
    Service Layer managing School-Level Platform Subscriptions (SCHOOL_PAYS Model).
    """

    @classmethod
    @transaction.atomic
    def calculate_and_provision_school_subscription(
        cls,
        tenant: Tenant,
        plan: SubscriptionPlan,
        duration_days: int = 120
    ) -> ServiceResult:
        """
        Calculates active enrolled student count, computes tier fee, and provisions a TenantSubscription.
        """
        try:
            # Calculate School Fee using BillingCalculationService
            calc_result = BillingCalculationService.calculate_school_fee(tenant=tenant, plan=plan)
            if not calc_result.success:
                raise SubscriptionException(calc_result.message)

            calc_data = calc_result.data
            active_students = calc_data.get("active_student_count", 0)
            calculated_amount = Decimal(str(calc_data.get("total_amount", 0.00)))

            start_date = timezone.now()
            end_date = start_date + timezone.timedelta(days=duration_days)
            grace_ends = end_date + timezone.timedelta(days=plan.grace_period_days)

            subscription, created = TenantSubscription.objects.get_or_create(
                tenant=tenant,
                defaults={
                    'plan': plan,
                    'billing_model': 'SCHOOL_PAYS',
                    'billing_cycle': 'TERMLY',
                    'status': 'ACTIVE',
                    'active_student_count': active_students,
                    'calculated_amount': calculated_amount,
                    'start_date': start_date,
                    'end_date': end_date,
                    'grace_period_ends_at': grace_ends
                }
            )

            if not created:
                subscription.plan = plan
                subscription.active_student_count = active_students
                subscription.calculated_amount = calculated_amount
                subscription.end_date = end_date
                subscription.grace_period_ends_at = grace_ends
                subscription.save(update_fields=[
                    'plan', 'active_student_count', 'calculated_amount',
                    'end_date', 'grace_period_ends_at'
                ])

            logger.info(f"School Subscription {'created' if created else 'updated'} for {tenant.name}: {active_students} students = ₦{calculated_amount}")
            return ServiceResult.ok(
                data={
                    "subscription_id": str(subscription.id),
                    "tenant_name": tenant.name,
                    "plan_name": plan.name,
                    "active_students": active_students,
                    "calculated_amount": float(calculated_amount),
                    "end_date": str(end_date),
                    "status": subscription.status
                },
                message="School subscription provisioned successfully."
            )

        except Exception as e:
            logger.error(f"Failed to provision school subscription for tenant {tenant.id}: {str(e)}")
            if isinstance(e, SubscriptionException):
                raise
            raise SubscriptionException(f"Failed to provision school subscription: {str(e)}") from e

    @classmethod
    @transaction.atomic
    def activate_school_parent_access(
        cls,
        tenant_subscription: TenantSubscription
    ) -> ServiceResult:
        """
        Activates parent and student access platform-wide for a school that completed subscription payment.
        """
        try:
            tenant = tenant_subscription.tenant
            tenant_subscription.status = 'ACTIVE'
            tenant_subscription.last_payment_date = timezone.now()
            tenant_subscription.save(update_fields=['status', 'last_payment_date'])

            tenant.billing_status = 'ACTIVE'
            tenant.save(update_fields=['billing_status'])

            logger.info(f"Activated platform-wide Parent & Student Access for School: {tenant.name}")
            return ServiceResult.ok(
                data={"tenant_id": str(tenant.id), "tenant_name": tenant.name, "status": "ACTIVE"},
                message="School Parent & Student Access activated successfully."
            )

        except Exception as e:
            logger.error(f"Failed to activate school parent access for tenant {tenant_subscription.tenant_id}: {str(e)}")
            raise SubscriptionException(f"Failed to activate school access: {str(e)}") from e

    @classmethod
    @transaction.atomic
    def suspend_school_parent_access(
        cls,
        tenant_subscription: TenantSubscription,
        reason: str = ""
    ) -> ServiceResult:
        """
        Suspends parent and student platform access for a non-compliant or expired school.
        """
        try:
            tenant = tenant_subscription.tenant
            tenant_subscription.status = 'SUSPENDED'
            tenant_subscription.save(update_fields=['status'])

            tenant.billing_status = 'SUSPENDED'
            tenant.save(update_fields=['billing_status'])

            logger.info(f"Suspended platform access for School {tenant.name}. Reason: {reason}")
            return ServiceResult.ok(
                data={"tenant_id": str(tenant.id), "status": "SUSPENDED"},
                message="School platform access suspended."
            )

        except Exception as e:
            logger.error(f"Failed to suspend school access for tenant {tenant_subscription.tenant_id}: {str(e)}")
            raise SubscriptionException(f"Failed to suspend school access: {str(e)}") from e
