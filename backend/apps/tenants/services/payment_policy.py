"""
Payment Policy & Pre-Condition Validation Engine for EduOrbit SaaS Platform.
Contains Pure Business Validation Rules determining whether an invoice or subscription can be paid.
NO payment gateway logic lives in this service.
"""

import logging
from decimal import Decimal
from typing import Optional
from django.db import transaction
from django.utils import timezone

from backend.apps.tenants.dto import ServiceResult
from backend.apps.tenants.exceptions import PaymentPolicyException
from backend.apps.tenants.models import SubscriptionInvoice, SubscriptionPayment, Tenant

logger = logging.getLogger(__name__)


class PaymentPolicyService:
    """
    Validation Policy Engine for Subscription Payments.
    """

    @classmethod
    def validate_invoice_payable(cls, invoice: SubscriptionInvoice) -> ServiceResult:
        """
        Validates if an invoice is in an acceptable state to receive payment.
        """
        try:
            if not invoice:
                return ServiceResult.fail("Invoice object is missing or null.")

            if invoice.status == 'PAID':
                return ServiceResult.fail("Invoice is already marked as PAID.", errors=["INVOICE_ALREADY_PAID"])

            if invoice.status == 'CANCELLED':
                return ServiceResult.fail("Cannot process payment for a CANCELLED invoice.", errors=["INVOICE_CANCELLED"])

            if invoice.status == 'DRAFT':
                return ServiceResult.fail("Invoice is currently in DRAFT status and cannot be paid.", errors=["INVOICE_IN_DRAFT"])

            if invoice.status not in ['PENDING', 'OVERDUE']:
                return ServiceResult.fail(f"Invalid invoice status for payment: {invoice.status}")

            if invoice.total_amount <= 0:
                return ServiceResult.fail("Invoice total amount must be greater than zero.")

            # Validate Tenant Status
            if invoice.tenant and invoice.tenant.billing_status == 'SUSPENDED':
                return ServiceResult.fail("Tenant account is SUSPENDED. Cannot process payment.", errors=["TENANT_SUSPENDED"])

            return ServiceResult.ok(
                data={"invoice_id": str(invoice.id), "invoice_number": invoice.invoice_number},
                message="Invoice is valid for payment."
            )

        except Exception as e:
            logger.error(f"Error validating invoice payable policy for invoice {invoice.id if invoice else 'N/A'}: {str(e)}")
            return ServiceResult.fail(f"Invoice validation failed: {str(e)}")

    @classmethod
    def validate_payment_amount(cls, invoice: SubscriptionInvoice, amount: Decimal) -> ServiceResult:
        """
        Validates that payment amount is positive and matches the invoice total.
        """
        try:
            if amount <= 0:
                return ServiceResult.fail("Payment amount must be greater than zero.", errors=["INVALID_AMOUNT"])

            if Decimal(str(amount)) != invoice.total_amount:
                return ServiceResult.fail(
                    f"Payment amount ₦{amount} does not match invoice total amount ₦{invoice.total_amount}.",
                    errors=["AMOUNT_MISMATCH"]
                )

            return ServiceResult.ok(message="Payment amount is valid.")

        except Exception as e:
            logger.error(f"Error validating payment amount for invoice {invoice.id}: {str(e)}")
            return ServiceResult.fail(f"Amount validation error: {str(e)}")

    @classmethod
    @transaction.atomic
    def validate_duplicate_payment(cls, invoice: SubscriptionInvoice, payment_reference: str) -> ServiceResult:
        """
        Checks for duplicate payment references using atomic database locks to prevent race conditions.
        """
        try:
            if not payment_reference:
                return ServiceResult.fail("Payment reference is required.", errors=["MISSING_REFERENCE"])

            existing_payment = SubscriptionPayment.objects.select_for_update().filter(
                reference=payment_reference
            ).first()

            if existing_payment:
                logger.warning(f"Duplicate payment reference detected: {payment_reference}")
                return ServiceResult.fail(
                    f"Payment reference '{payment_reference}' has already been processed.",
                    errors=["DUPLICATE_PAYMENT_REFERENCE"],
                    data={"existing_status": existing_payment.status}
                )

            return ServiceResult.ok(message="Payment reference is unique and clear for processing.")

        except Exception as e:
            logger.error(f"Error validating duplicate payment reference '{payment_reference}': {str(e)}")
            return ServiceResult.fail(f"Duplicate check failed: {str(e)}")
