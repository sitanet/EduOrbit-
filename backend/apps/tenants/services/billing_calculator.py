"""
Billing & Pricing Calculation Engine for EduOrbit SaaS Platform.
Single Source of Truth for all Parent & School Subscription Calculations.
"""

import logging
from decimal import Decimal
from typing import Dict, Any, Optional
from django.utils import timezone

from backend.apps.tenants.dto import ServiceResult
from backend.apps.tenants.exceptions import BillingException
from backend.apps.people.models import ParentProfile, FamilyRelationship, StudentProfile
from backend.apps.tenants.models import Tenant, SubscriptionPlan

logger = logging.getLogger(__name__)


class BillingCalculationService:
    """
    Pure Calculation Engine enforcing EduOrbit Billing Rules:
    1. Parent Pays Model: Billing is strictly PER ACTIVE CHILD.
       Only students with enrollment_status='enrolled' are counted.
       Withdrawn, graduated, or inactive students are NOT billed.
    2. School Pays Model: Pricing computed based on total active student count and tier rates.
    """

    @classmethod
    def calculate_parent_fee(
        cls,
        parent_profile: ParentProfile,
        fee_per_child: Decimal,
        discount_percent: Decimal = Decimal("0.00"),
        tax_percent: Decimal = Decimal("0.00")
    ) -> ServiceResult:
        """
        Calculates parent subscription subtotal, discount, tax, and total amount based on active enrolled children.
        """
        try:
            if fee_per_child < 0:
                raise BillingException("Base fee per child cannot be negative.")

            # Filter relationships where the linked student is active & currently enrolled
            family_links = FamilyRelationship.objects.filter(
                relative=parent_profile.person,
                student__student_profile__isnull=False,
                student__student_profile__enrollment_status='enrolled'
            )
            
            active_child_count = family_links.count()

            if active_child_count == 0:
                logger.info(f"Parent {parent_profile.parent_number} has 0 active enrolled children.")

            subtotal = fee_per_child * Decimal(str(active_child_count))
            discount = subtotal * (discount_percent / Decimal("100.00"))
            taxable_amount = subtotal - discount
            tax = taxable_amount * (tax_percent / Decimal("100.00"))
            total = taxable_amount + tax

            snapshot = {
                "parent_number": parent_profile.parent_number,
                "active_child_count": active_child_count,
                "fee_per_child": float(fee_per_child),
                "subtotal": float(subtotal),
                "discount_percent": float(discount_percent),
                "discount_amount": float(discount),
                "tax_percent": float(tax_percent),
                "tax_amount": float(tax),
                "total_amount": float(total),
                "calculated_at": str(timezone.now())
            }

            logger.info(
                f"Calculated Parent Fee for {parent_profile.parent_number}: "
                f"{active_child_count} children @ ₦{fee_per_child} = ₦{total}"
            )
            return ServiceResult.ok(data=snapshot, message="Parent fee calculation completed successfully.")

        except Exception as e:
            logger.error(f"Error calculating parent fee for parent {parent_profile.id}: {str(e)}")
            if isinstance(e, BillingException):
                raise
            raise BillingException(f"Failed to calculate parent subscription fee: {str(e)}") from e

    @classmethod
    def calculate_school_fee(
        cls,
        tenant: Tenant,
        plan: SubscriptionPlan,
        custom_active_students: Optional[int] = None
    ) -> ServiceResult:
        """
        Calculates school termly subscription fee using active student count and pricing tiers.
        """
        try:
            if custom_active_students is not None:
                active_student_count = custom_active_students
            else:
                active_student_count = StudentProfile.objects.filter(
                    tenant=tenant,
                    enrollment_status='enrolled'
                ).count()

            tier_rates = plan.student_tier_rates or {}
            rate_per_student = Decimal("0.00")

            # Evaluate Tier Rates (e.g. {'1-200': 2000, '201-500': 1500, '501-1000': 1200, '1001+': 1000})
            if tier_rates:
                for tier_key, rate in tier_rates.items():
                    if '-' in tier_key:
                        low, high = map(int, tier_key.split('-'))
                        if low <= active_student_count <= high:
                            rate_per_student = Decimal(str(rate))
                            break
                    elif tier_key.endswith('+'):
                        low = int(tier_key.replace('+', ''))
                        if active_student_count >= low:
                            rate_per_student = Decimal(str(rate))
                            break

            if rate_per_student == 0 and plan.termly_price > 0:
                subtotal = plan.termly_price
            else:
                subtotal = rate_per_student * Decimal(str(active_student_count))

            snapshot = {
                "tenant_name": tenant.name,
                "plan_name": plan.name,
                "active_student_count": active_student_count,
                "rate_per_student": float(rate_per_student),
                "subtotal": float(subtotal),
                "tax_amount": 0.00,
                "total_amount": float(subtotal),
                "calculated_at": str(timezone.now())
            }

            logger.info(
                f"Calculated School Fee for {tenant.name}: "
                f"{active_student_count} students = ₦{subtotal}"
            )
            return ServiceResult.ok(data=snapshot, message="School fee calculation completed successfully.")

        except Exception as e:
            logger.error(f"Error calculating school fee for tenant {tenant.id}: {str(e)}")
            raise BillingException(f"Failed to calculate school subscription fee: {str(e)}") from e
