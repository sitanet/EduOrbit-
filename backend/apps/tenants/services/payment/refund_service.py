"""
Refund Management & Lifecycle Service for EduOrbit SaaS ERP.
Manages refund states (REQUESTED -> APPROVED -> PROCESSING -> COMPLETED -> FAILED / CANCELLED).
Reverses receipts, invoices, and subscriptions ONLY upon refund completion.
"""

import logging
from typing import Optional
from django.db import transaction
from django.utils import timezone

from backend.apps.tenants.dto import ServiceResult
from backend.apps.tenants.models import SubscriptionPayment, ParentSubscription
from backend.apps.tenants.services.audit_service import AuditService

logger = logging.getLogger(__name__)


class RefundService:
    """
    Service managing support refund requests, approvals, and subscription reversals.
    """

    @classmethod
    @transaction.atomic
    def request_refund(cls, payment: SubscriptionPayment, reason: str = "", actor=None) -> ServiceResult:
        """
        Marks payment as REFUND_REQUESTED.
        """
        if payment.status != 'SUCCESSFUL':
            return ServiceResult.fail(f"Only SUCCESSFUL payments can be refunded. Current status: {payment.status}")

        payment.status = 'REFUND_REQUESTED'
        payment.failure_reason = f"Refund requested: {reason}"
        payment.save(update_fields=['status', 'failure_reason'])

        AuditService.log_event(
            action="REFUND_REQUESTED",
            tenant=payment.tenant,
            invoice=payment.invoice,
            payment=payment,
            actor=actor,
            notes=f"Refund requested. Reason: {reason}"
        )
        return ServiceResult.ok(data={"payment_id": str(payment.id)}, message="Refund request submitted successfully.")

    @classmethod
    @transaction.atomic
    def approve_and_process_refund(cls, payment: SubscriptionPayment, actor=None) -> ServiceResult:
        """
        Approves and completes refund, reversing invoice, receipt, and parent subscription.
        """
        if payment.status not in ['REFUND_REQUESTED', 'SUCCESSFUL']:
            return ServiceResult.fail(f"Payment status '{payment.status}' is not eligible for refund approval.")

        payment.status = 'REFUNDED'
        payment.completed_at = timezone.now()
        payment.save(update_fields=['status', 'completed_at'])

        # Reverse Invoice status
        invoice = payment.invoice
        if invoice:
            invoice.status = 'CANCELLED'
            invoice.save(update_fields=['status'])

            # Deactivate linked parent subscription
            for parent_sub in invoice.parent_subscriptions.all():
                parent_sub.status = 'CANCELLED'
                parent_sub.save(update_fields=['status'])
                parent_sub.activated_students.update(payment_status='CANCELLED')

        AuditService.log_event(
            action="REFUNDED",
            tenant=payment.tenant,
            invoice=invoice,
            payment=payment,
            actor=actor,
            notes="Refund approved and subscription cancelled."
        )
        return ServiceResult.ok(data={"payment_id": str(payment.id)}, message="Refund approved and processed successfully.")
