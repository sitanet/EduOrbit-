"""
Invoice Lifecycle Management Engine for EduOrbit SaaS Platform.
Handles atomic invoice generation, status transitions, balance calculations, and historical preservation.
"""

import logging
import uuid
from decimal import Decimal
from typing import Optional
from django.db import transaction
from django.utils import timezone

from backend.apps.tenants.dto import ServiceResult
from backend.apps.tenants.exceptions import InvoiceException
from backend.apps.tenants.models import Tenant, School, SubscriptionInvoice, ParentSubscription, TenantSubscription

logger = logging.getLogger(__name__)


class InvoiceService:
    """
    Service layer controlling Subscription Invoices.
    Ensures sequential invoice numbering, double-invoicing protection, and immutable paid invoices.
    """

    @classmethod
    def generate_invoice_number(cls, prefix: str = "INV-") -> str:
        """
        Generates unique, sequential-formatted invoice identifier (e.g., INV-20260803-AB12).
        """
        datestr = timezone.now().strftime("%Y%m%d")
        short_id = str(uuid.uuid4())[:6].upper()
        return f"{prefix}{datestr}-{short_id}"

    @classmethod
    @transaction.atomic
    def create_parent_invoice(
        cls,
        tenant: Tenant,
        school: School,
        parent_subscription: ParentSubscription,
        amount: Decimal,
        due_days: int = 14
    ) -> ServiceResult:
        """
        Atomically generates a pending Parent Access Invoice.
        Prevents duplicate pending invoices for the same parent subscription.
        """
        try:
            if amount < 0:
                raise InvoiceException("Invoice amount cannot be negative.")

            # Concurrency Protection: Check for existing pending invoice
            existing_invoice = SubscriptionInvoice.objects.select_for_update().filter(
                tenant=tenant,
                parent_subscriptions=parent_subscription,
                status='PENDING'
            ).first()

            if existing_invoice:
                logger.info(f"Existing pending invoice found: {existing_invoice.invoice_number}")
                return ServiceResult.ok(
                    data={"invoice_id": str(existing_invoice.id), "invoice_number": existing_invoice.invoice_number},
                    message="Pending invoice already exists."
                )

            inv_number = cls.generate_invoice_number(prefix="INV-PAR-")
            due_date = timezone.now() + timezone.timedelta(days=due_days)

            invoice = SubscriptionInvoice.objects.create(
                tenant=tenant,
                school=school,
                invoice_number=inv_number,
                invoice_type='PARENT',
                amount=amount,
                tax_amount=Decimal("0.00"),
                total_amount=amount,
                status='PENDING',
                due_date=due_date
            )

            parent_subscription.invoice = invoice
            parent_subscription.save(update_fields=['invoice'])

            logger.info(f"Created Parent Invoice {inv_number} for amount ₦{amount}")
            return ServiceResult.ok(
                data={"invoice_id": str(invoice.id), "invoice_number": invoice.invoice_number, "amount": float(amount)},
                message="Parent Invoice created successfully."
            )

        except Exception as e:
            logger.error(f"Failed to create parent invoice: {str(e)}")
            if isinstance(e, InvoiceException):
                raise
            raise InvoiceException(f"Failed to create parent invoice: {str(e)}") from e

    @classmethod
    @transaction.atomic
    def create_school_invoice(
        cls,
        tenant: Tenant,
        school: School,
        tenant_subscription: TenantSubscription,
        amount: Decimal,
        due_days: int = 14
    ) -> ServiceResult:
        """
        Atomically generates a pending School Activation Invoice for SCHOOL_PAYS model.
        """
        try:
            if amount < 0:
                raise InvoiceException("Invoice amount cannot be negative.")

            existing_invoice = SubscriptionInvoice.objects.select_for_update().filter(
                tenant=tenant,
                tenant_subscription=tenant_subscription,
                status='PENDING'
            ).first()

            if existing_invoice:
                return ServiceResult.ok(
                    data={"invoice_id": str(existing_invoice.id), "invoice_number": existing_invoice.invoice_number},
                    message="Pending school invoice already exists."
                )

            inv_number = cls.generate_invoice_number(prefix="INV-SCH-")
            due_date = timezone.now() + timezone.timedelta(days=due_days)

            invoice = SubscriptionInvoice.objects.create(
                tenant=tenant,
                school=school,
                tenant_subscription=tenant_subscription,
                invoice_number=inv_number,
                invoice_type='SCHOOL',
                amount=amount,
                tax_amount=Decimal("0.00"),
                total_amount=amount,
                status='PENDING',
                due_date=due_date
            )

            logger.info(f"Created School Invoice {inv_number} for amount ₦{amount}")
            return ServiceResult.ok(
                data={"invoice_id": str(invoice.id), "invoice_number": invoice.invoice_number, "amount": float(amount)},
                message="School Invoice created successfully."
            )

        except Exception as e:
            logger.error(f"Failed to create school invoice: {str(e)}")
            if isinstance(e, InvoiceException):
                raise
            raise InvoiceException(f"Failed to create school invoice: {str(e)}") from e

    @classmethod
    @transaction.atomic
    def mark_invoice_paid(cls, invoice: SubscriptionInvoice) -> ServiceResult:
        """
        Atomically updates invoice status to PAID with paid timestamp.
        """
        try:
            # Lock invoice row
            inv = SubscriptionInvoice.objects.select_for_update().get(id=invoice.id)

            if inv.status == 'PAID':
                return ServiceResult.ok(
                    data={"invoice_id": str(inv.id), "status": inv.status},
                    message="Invoice is already marked as PAID."
                )

            if inv.status == 'CANCELLED':
                raise InvoiceException("Cannot mark a CANCELLED invoice as PAID.")

            inv.status = 'PAID'
            inv.paid_date = timezone.now()
            inv.save(update_fields=['status', 'paid_date'])

            logger.info(f"Invoice {inv.invoice_number} marked as PAID at {inv.paid_date}")
            return ServiceResult.ok(
                data={"invoice_id": str(inv.id), "invoice_number": inv.invoice_number, "paid_date": str(inv.paid_date)},
                message="Invoice marked as PAID successfully."
            )

        except Exception as e:
            logger.error(f"Failed to mark invoice {invoice.id} as paid: {str(e)}")
            if isinstance(e, InvoiceException):
                raise
            raise InvoiceException(f"Failed to mark invoice as paid: {str(e)}") from e

    @classmethod
    @transaction.atomic
    def cancel_invoice(cls, invoice: SubscriptionInvoice, reason: str = "") -> ServiceResult:
        """
        Cancels an unpaid invoice safely.
        """
        try:
            inv = SubscriptionInvoice.objects.select_for_update().get(id=invoice.id)

            if inv.status == 'PAID':
                raise InvoiceException("Cannot cancel an invoice that has already been PAID.")

            inv.status = 'CANCELLED'
            inv.save(update_fields=['status'])

            logger.info(f"Invoice {inv.invoice_number} CANCELLED. Reason: {reason}")
            return ServiceResult.ok(
                data={"invoice_id": str(inv.id), "status": inv.status},
                message="Invoice cancelled successfully."
            )

        except Exception as e:
            logger.error(f"Failed to cancel invoice {invoice.id}: {str(e)}")
            if isinstance(e, InvoiceException):
                raise
            raise InvoiceException(f"Failed to cancel invoice: {str(e)}") from e
