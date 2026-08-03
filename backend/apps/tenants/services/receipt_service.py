"""
Receipt Generation Engine for EduOrbit SaaS Platform.
Handles receipt creation, receipt numbering, and payment metadata linkage.
"""

import logging
import uuid
from typing import Optional
from django.db import transaction
from django.utils import timezone

from backend.apps.tenants.dto import ServiceResult
from backend.apps.tenants.exceptions import InvoiceException
from backend.apps.tenants.models import SubscriptionInvoice, SubscriptionPayment

logger = logging.getLogger(__name__)


class ReceiptService:
    """
    Receipt Management Service creating immutable proof of payment records.
    """

    @classmethod
    def generate_receipt_number(cls, prefix: str = "REC-") -> str:
        """
        Generates a unique sequential receipt number string (e.g. REC-20260803-XY99).
        """
        datestr = timezone.now().strftime("%Y%m%d")
        short_id = str(uuid.uuid4())[:6].upper()
        return f"{prefix}{datestr}-{short_id}"

    @classmethod
    @transaction.atomic
    def create_receipt(
        cls,
        payment: SubscriptionPayment,
        invoice: SubscriptionInvoice
    ) -> ServiceResult:
        """
        Generates and assigns an official receipt number to a successful payment.
        """
        try:
            if payment.status != 'SUCCESSFUL':
                raise InvoiceException(f"Cannot generate receipt for unsuccessful payment status: {payment.status}")

            if payment.receipt_number:
                logger.info(f"Payment {payment.reference} already has receipt: {payment.receipt_number}")
                return ServiceResult.ok(
                    data={"receipt_number": payment.receipt_number, "payment_reference": payment.reference},
                    message="Receipt already exists."
                )

            receipt_num = cls.generate_receipt_number()
            payment.receipt_number = receipt_num
            payment.save(update_fields=['receipt_number'])

            receipt_snapshot = {
                "receipt_number": receipt_num,
                "payment_reference": payment.reference,
                "invoice_number": invoice.invoice_number,
                "amount": float(payment.amount),
                "payment_method": payment.payment_method,
                "paid_at": str(payment.paid_at or timezone.now()),
                "tenant_id": str(payment.tenant_id)
            }

            logger.info(f"Receipt {receipt_num} created for payment {payment.reference}")
            return ServiceResult.ok(
                data=receipt_snapshot,
                message="Receipt generated successfully."
            )

        except Exception as e:
            logger.error(f"Failed to generate receipt for payment {payment.id}: {str(e)}")
            if isinstance(e, InvoiceException):
                raise
            raise InvoiceException(f"Failed to generate receipt: {str(e)}") from e
