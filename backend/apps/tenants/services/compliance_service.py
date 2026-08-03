"""
School Payment Compliance Engine for EduOrbit SaaS Platform.
Calculates payment compliance percentages, outstanding parent counts, and evaluates policy restrictions.
"""

import logging
from decimal import Decimal
from typing import Optional, Dict, Any
from django.utils import timezone

from backend.apps.tenants.dto import ServiceResult
from backend.apps.tenants.exceptions import ComplianceException
from backend.apps.tenants.models import Tenant, ParentSubscription, StudentPlatformSubscription
from backend.apps.people.models import ParentProfile, StudentProfile, FamilyRelationship
from backend.apps.academic.models import AcademicPeriod

logger = logging.getLogger(__name__)


class ComplianceService:
    """
    Evaluates School Parent Payment Compliance under Model 1 (PARENT_PAYS).
    """

    @classmethod
    def calculate_school_compliance_metrics(
        cls,
        tenant: Tenant,
        academic_period: Optional[AcademicPeriod] = None
    ) -> ServiceResult:
        """
        Calculates parent payment compliance statistics and evaluates compliance status.
        """
        try:
            threshold = tenant.compliance_threshold_percent or Decimal("80.00")

            # Get all active enrolled students for tenant
            active_students = StudentProfile.objects.filter(
                tenant=tenant,
                enrollment_status='enrolled'
            )
            total_students_count = active_students.count()

            # Resolve unique parent profiles linked to active enrolled students
            parent_ids = FamilyRelationship.objects.filter(
                tenant=tenant,
                student__in=[s.person for s in active_students]
            ).values_list('relative__parent_profile__id', flat=True).distinct()

            parent_ids = [pid for pid in parent_ids if pid is not None]
            total_parents_count = len(parent_ids)

            # Count paid parents for academic period
            paid_sub_query = ParentSubscription.objects.filter(
                tenant=tenant,
                parent_id__in=parent_ids,
                status='ACTIVE'
            )
            if academic_period:
                paid_sub_query = paid_sub_query.filter(academic_period=academic_period)

            paid_parents_count = paid_sub_query.values('parent').distinct().count()
            unpaid_parents_count = max(0, total_parents_count - paid_parents_count)

            if total_parents_count > 0:
                payment_percentage = Decimal(str(round((paid_parents_count / total_parents_count) * 100, 2)))
            else:
                payment_percentage = Decimal("100.00")

            # Determine compliance status
            if payment_percentage >= threshold:
                compliance_status = 'COMPLIANT'
            elif tenant.billing_status == 'GRACE_PERIOD':
                compliance_status = 'GRACE_PERIOD'
            else:
                compliance_status = 'RESTRICTED'

            metrics = {
                "tenant_name": tenant.name,
                "compliance_threshold_percent": float(threshold),
                "total_active_students": total_students_count,
                "total_parents": total_parents_count,
                "paid_parents": paid_parents_count,
                "unpaid_parents": unpaid_parents_count,
                "payment_percentage": float(payment_percentage),
                "compliance_status": compliance_status,
                "evaluated_at": str(timezone.now())
            }

            logger.info(f"Compliance metrics for {tenant.name}: {payment_percentage}% paid (Threshold: {threshold}%) -> {compliance_status}")
            return ServiceResult.ok(
                data=metrics,
                message="Compliance evaluation completed successfully."
            )

        except Exception as e:
            logger.error(f"Failed to calculate compliance for tenant {tenant.id}: {str(e)}")
            raise ComplianceException(f"Failed to calculate compliance: {str(e)}") from e
