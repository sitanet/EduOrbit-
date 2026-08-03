"""
Parent Subscription Lifecycle Service for EduOrbit SaaS Platform.
Controls single Parent Subscription licensing and activation of ALL linked active enrolled children.
"""

import logging
from decimal import Decimal
from typing import Optional, Dict, Any
from django.db import transaction
from django.utils import timezone

from backend.apps.tenants.dto import ServiceResult
from backend.apps.tenants.exceptions import SubscriptionException
from backend.apps.people.models import ParentProfile, StudentProfile, FamilyRelationship
from backend.apps.tenants.models import ParentSubscription, StudentPlatformSubscription, TenantSubscription
from backend.apps.academic.models import AcademicPeriod, AcademicYear

logger = logging.getLogger(__name__)


class ParentSubscriptionService:
    """
    Core Domain Service managing Parent Access Licensing.
    """

    @classmethod
    @transaction.atomic
    def create_or_get_parent_subscription(
        cls,
        parent_profile: ParentProfile,
        academic_period: Optional[AcademicPeriod] = None,
        fee_per_child: Decimal = Decimal("5000.00")
    ) -> ServiceResult:
        """
        Retrieves or initializes a ParentSubscription record for a given academic period.
        Calculates active child count and updates subscription total amount.
        """
        try:
            tenant = parent_profile.tenant
            
            # Count active enrolled children
            active_child_links = FamilyRelationship.objects.filter(
                relative=parent_profile.person,
                student__student_profile__isnull=False,
                student__student_profile__enrollment_status='enrolled'
            )
            child_count = active_child_links.count()

            parent_sub, created = ParentSubscription.objects.get_or_create(
                tenant=tenant,
                parent=parent_profile,
                academic_period=academic_period,
                defaults={
                    'child_count': child_count,
                    'fee_per_child': fee_per_child,
                    'status': 'UNPAID',
                    'amount': fee_per_child * Decimal(str(child_count))
                }
            )

            if not created:
                parent_sub.child_count = child_count
                parent_sub.fee_per_child = fee_per_child
                parent_sub.calculate_total_amount()
                parent_sub.save(update_fields=['child_count', 'fee_per_child', 'amount'])

            logger.info(f"ParentSubscription {'created' if created else 'retrieved'} for {parent_profile.parent_number}: Total ₦{parent_sub.amount}")
            return ServiceResult.ok(
                data={
                    "parent_subscription_id": str(parent_sub.id),
                    "parent_number": parent_profile.parent_number,
                    "child_count": child_count,
                    "fee_per_child": float(fee_per_child),
                    "total_amount": float(parent_sub.amount),
                    "status": parent_sub.status
                },
                message="Parent subscription initialized successfully."
            )

        except Exception as e:
            logger.error(f"Error initializing parent subscription for {parent_profile.id}: {str(e)}")
            raise SubscriptionException(f"Failed to create parent subscription: {str(e)}") from e

    @classmethod
    @transaction.atomic
    def activate_parent_subscription(
        cls,
        parent_subscription: ParentSubscription,
        duration_days: int = 120
    ) -> ServiceResult:
        """
        Activates a Parent Subscription and sets StudentPlatformSubscription status to ACTIVE
        for ALL active enrolled children linked to this parent account.
        """
        try:
            now = timezone.now()
            paid_until = now + timezone.timedelta(days=duration_days)

            parent_subscription.status = 'ACTIVE'
            parent_subscription.paid_until = paid_until
            parent_subscription.save(update_fields=['status', 'paid_until'])

            # Find all active enrolled children linked to this parent
            family_links = FamilyRelationship.objects.filter(
                relative=parent_subscription.parent.person,
                student__student_profile__isnull=False,
                student__student_profile__enrollment_status='enrolled'
            )

            activated_student_ids = []
            for link in family_links:
                student_profile = link.student.student_profile
                stu_sub, _ = StudentPlatformSubscription.objects.get_or_create(
                    tenant=parent_subscription.tenant,
                    student=student_profile,
                    defaults={
                        'parent_subscription': parent_subscription,
                        'payment_status': 'ACTIVE',
                        'paid_until': paid_until,
                        'amount': Decimal("0.00")
                    }
                )
                stu_sub.parent_subscription = parent_subscription
                stu_sub.payment_status = 'ACTIVE'
                stu_sub.paid_until = paid_until
                stu_sub.save(update_fields=['parent_subscription', 'payment_status', 'paid_until'])
                activated_student_ids.append(str(student_profile.id))

            logger.info(f"Activated Parent Subscription {parent_subscription.id} for {len(activated_student_ids)} children until {paid_until}")
            return ServiceResult.ok(
                data={
                    "parent_subscription_id": str(parent_subscription.id),
                    "status": "ACTIVE",
                    "paid_until": str(paid_until),
                    "activated_students_count": len(activated_student_ids)
                },
                message=f"Parent subscription activated. {len(activated_student_ids)} children enabled."
            )

        except Exception as e:
            logger.error(f"Failed to activate parent subscription {parent_subscription.id}: {str(e)}")
            raise SubscriptionException(f"Failed to activate parent subscription: {str(e)}") from e

    @classmethod
    def check_parent_access_status(
        cls,
        parent_profile: ParentProfile,
        academic_period: Optional[AcademicPeriod] = None
    ) -> ServiceResult:
        """
        Checks if parent account access is active.
        If Tenant billing model is SCHOOL_PAYS, checks school-level TenantSubscription status.
        If Tenant billing model is PARENT_PAYS, checks parent's ParentSubscription status.
        """
        try:
            tenant = parent_profile.tenant

            # School Pays Model Check
            if tenant.billing_model == 'SCHOOL_PAYS':
                tenant_sub = TenantSubscription.objects.filter(tenant=tenant).first()
                if tenant_sub and tenant_sub.is_active_license():
                    return ServiceResult.ok(
                        data={"is_active": True, "reason": "SCHOOL_PAYS_ACTIVE", "billing_model": "SCHOOL_PAYS"},
                        message="Parent access granted via School Subscription."
                    )
                return ServiceResult.fail(
                    message="Parent access suspended: School subscription is unpaid or expired.",
                    errors=["SCHOOL_SUBSCRIPTION_INACTIVE"],
                    data={"is_active": False, "billing_model": "SCHOOL_PAYS"}
                )

            # Parent Pays Model Check
            sub_query = ParentSubscription.objects.filter(tenant=tenant, parent=parent_profile)
            if academic_period:
                sub_query = sub_query.filter(academic_period=academic_period)

            parent_sub = sub_query.order_by('-created_at').first()

            if not parent_sub:
                return ServiceResult.fail(
                    message="No subscription found for this parent account.",
                    errors=["SUBSCRIPTION_NOT_FOUND"],
                    data={"is_active": False, "billing_model": "PARENT_PAYS"}
                )

            now = timezone.now()
            if parent_sub.status == 'ACTIVE' and parent_sub.paid_until and parent_sub.paid_until > now:
                return ServiceResult.ok(
                    data={
                        "is_active": True,
                        "status": parent_sub.status,
                        "paid_until": str(parent_sub.paid_until),
                        "child_count": parent_sub.child_count,
                        "billing_model": "PARENT_PAYS"
                    },
                    message="Parent access is active."
                )

            return ServiceResult.fail(
                message="Parent subscription is unpaid or expired.",
                errors=["SUBSCRIPTION_EXPIRED"],
                data={
                    "is_active": False,
                    "status": parent_sub.status,
                    "billing_model": "PARENT_PAYS",
                    "paid_until": str(parent_sub.paid_until) if parent_sub.paid_until else None
                }
            )

        except Exception as e:
            logger.error(f"Error checking parent access status for {parent_profile.id}: {str(e)}")
            return ServiceResult.fail(f"Failed to check access status: {str(e)}")

    @classmethod
    def check_student_access_status(
        cls,
        student_profile: StudentProfile,
        academic_period: Optional[AcademicPeriod] = None
    ) -> ServiceResult:
        """
        Checks if student portal/app access is active.
        """
        try:
            tenant = student_profile.tenant

            if tenant.billing_model == 'SCHOOL_PAYS':
                tenant_sub = TenantSubscription.objects.filter(tenant=tenant).first()
                if tenant_sub and tenant_sub.is_active_license():
                    return ServiceResult.ok(
                        data={"is_active": True, "reason": "SCHOOL_PAYS_ACTIVE"},
                        message="Student access granted via School Subscription."
                    )
                return ServiceResult.fail(
                    message="Student access suspended: School subscription is unpaid or expired.",
                    errors=["SCHOOL_SUBSCRIPTION_INACTIVE"],
                    data={"is_active": False}
                )

            # Check StudentPlatformSubscription
            stu_sub = StudentPlatformSubscription.objects.filter(
                tenant=tenant,
                student=student_profile,
                payment_status='ACTIVE'
            ).order_by('-created_at').first()

            if stu_sub and (not stu_sub.paid_until or stu_sub.paid_until > timezone.now()):
                return ServiceResult.ok(
                    data={"is_active": True, "paid_until": str(stu_sub.paid_until)},
                    message="Student access is active."
                )

            return ServiceResult.fail(
                message="Student access unavailable: Linked parent subscription is unpaid or expired.",
                errors=["PARENT_SUBSCRIPTION_REQUIRED"],
                data={"is_active": False}
            )

        except Exception as e:
            logger.error(f"Error checking student access status for {student_profile.id}: {str(e)}")
            return ServiceResult.fail(f"Failed to check student status: {str(e)}")
