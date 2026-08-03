"""
Centralized Immutable Audit Logging Service for EduOrbit SaaS Platform.
Records business subscription events, payments, status transitions, manual overrides, and invoicing actions.
"""

import logging
from typing import Optional
from django.utils import timezone

from backend.apps.tenants.dto import ServiceResult
from backend.apps.tenants.models import (
    Tenant, TenantSubscription, ParentSubscription, SubscriptionInvoice, SubscriptionPayment, SubscriptionAuditLog
)
from backend.apps.identity.models import User

logger = logging.getLogger(__name__)


class AuditService:
    """
    Centralized Database Audit Logger for Subscription System.
    """

    @classmethod
    def log_event(
        cls,
        action: str,
        tenant: Optional[Tenant] = None,
        tenant_subscription: Optional[TenantSubscription] = None,
        parent_subscription: Optional[ParentSubscription] = None,
        invoice: Optional[SubscriptionInvoice] = None,
        payment: Optional[SubscriptionPayment] = None,
        actor: Optional[User] = None,
        ip_address: Optional[str] = None,
        notes: str = ""
    ) -> ServiceResult:
        """
        Creates an immutable SubscriptionAuditLog record in database.
        """
        try:
            # Resolve tenant
            target_tenant = tenant
            if not target_tenant and tenant_subscription:
                target_tenant = tenant_subscription.tenant
            elif not target_tenant and parent_subscription:
                target_tenant = parent_subscription.tenant
            elif not target_tenant and invoice:
                target_tenant = invoice.tenant
            elif not target_tenant and payment:
                target_tenant = payment.tenant

            audit_log = SubscriptionAuditLog.objects.create(
                tenant=target_tenant,
                action=action,
                tenant_subscription=tenant_subscription,
                parent_subscription=parent_subscription,
                invoice=invoice,
                payment=payment,
                actor=actor,
                timestamp=timezone.now(),
                ip_address=ip_address,
                notes=notes
            )

            logger.info(f"Audit Log Recorded [{action}]: {notes} (ID: {audit_log.id})")
            return ServiceResult.ok(
                data={"audit_log_id": str(audit_log.id), "action": action, "timestamp": str(audit_log.timestamp)},
                message="Audit log entry created."
            )

        except Exception as e:
            logger.error(f"Failed to record audit log entry for action '{action}': {str(e)}")
            # Return fail result without crashing main workflow
            return ServiceResult.fail(f"Audit logging failed: {str(e)}")
