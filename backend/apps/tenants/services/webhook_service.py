"""
Gateway Webhook Processing Engine for EduOrbit SaaS Platform.
Handles secure signature verification, payload normalization, idempotent duplicate webhook protection,
and workflow delegation for Paystack & OPay.
"""

import logging
from typing import Dict, Any, Optional
from django.db import transaction

from backend.apps.tenants.dto import ServiceResult
from backend.apps.tenants.exceptions import PaymentPolicyException
from backend.apps.tenants.models import SubscriptionInvoice, SubscriptionPayment
from backend.apps.tenants.services.payment_gateway import PaymentGatewayFactory
from backend.apps.tenants.services.subscription_workflow import SubscriptionWorkflowService
from backend.apps.tenants.services.audit_service import AuditService

logger = logging.getLogger(__name__)


class WebhookService:
    """
    Secure Idempotent Webhook Handler for Multi-Gateway Integration.
    """

    @classmethod
    @transaction.atomic
    def process_gateway_webhook(
        cls,
        provider_name: str,
        payload: Dict[str, Any],
        signature_header: str
    ) -> ServiceResult:
        """
        Processes incoming webhook event from Paystack or OPay:
        1. Validates HMAC signature.
        2. Normalizes response to extract reference, amount, and event type.
        3. Locks payment record row (`select_for_update`) to guarantee idempotency.
        4. Invokes SubscriptionWorkflowService to complete invoice payment, receipt, and account activation.
        """
        provider = str(provider_name).strip().upper()
        logger.info(f"Received webhook callback from provider: {provider}")

        try:
            # Step 1: Resolve Gateway & Verify Webhook Signature
            gateway = PaymentGatewayFactory.get_gateway(provider)
            is_valid_sig = gateway.verify_webhook_signature(payload=payload, signature_header=signature_header)

            if not is_valid_sig:
                logger.warning(f"Invalid webhook signature received for provider {provider}")
                return ServiceResult.fail("Invalid HMAC webhook signature.", errors=["INVALID_SIGNATURE"])

            # Step 2: Normalize Response Payload
            norm = gateway.normalize_response(payload)
            reference = norm.get("reference")
            is_success = norm.get("is_success")

            if not reference:
                return ServiceResult.fail("Webhook payload missing transaction reference.", errors=["MISSING_REFERENCE"])

            if not is_success:
                logger.info(f"Ignored non-successful webhook event '{norm.get('event_type')}' for ref {reference}")
                return ServiceResult.ok(
                    data={"reference": reference, "status": "ignored"},
                    message="Webhook event ignored (non-successful payment)."
                )

            # Step 3: Atomic Idempotency Lock
            payment = SubscriptionPayment.objects.select_for_update().filter(reference=reference).first()

            if payment and payment.status == 'SUCCESSFUL':
                logger.info(f"Idempotent Webhook: Payment {reference} is already processed & SUCCESSFUL.")
                return ServiceResult.ok(
                    data={"reference": reference, "status": "ALREADY_PROCESSED"},
                    message="Webhook payload already processed idempotently."
                )

            # Find matching invoice by reference or payment record
            invoice = payment.invoice if payment else SubscriptionInvoice.objects.filter(
                invoice_number__icontains=reference.split('-')[1] if '-' in reference and len(reference.split('-')) > 1 else ''
            ).first()

            if not invoice:
                logger.error(f"Webhook error: No invoice found for reference {reference}")
                return ServiceResult.fail(f"No invoice found matching reference {reference}.")

            # Step 4: Delegate to Workflow Service
            if invoice.invoice_type == 'PARENT':
                wf_result = SubscriptionWorkflowService.complete_parent_payment_workflow(
                    invoice=invoice,
                    payment_reference=reference,
                    payment_method=provider,
                    actor=payment.paid_by if payment else None
                )
            else:
                wf_result = SubscriptionWorkflowService.complete_school_payment_workflow(
                    invoice=invoice,
                    payment_reference=reference,
                    payment_method=provider,
                    actor=payment.paid_by if payment else None
                )

            if not wf_result.success:
                return wf_result

            # Update raw payload on payment record
            if payment:
                payment.raw_response = payload
                payment.save(update_fields=['raw_response'])

            AuditService.log_event(
                action="PAYMENT",
                tenant=invoice.tenant,
                invoice=invoice,
                payment=payment,
                notes=f"Webhook successfully processed for provider {provider}. Reference: {reference}"
            )

            logger.info(f"Webhook for {provider} ref {reference} processed successfully.")
            return ServiceResult.ok(
                data={"provider": provider, "reference": reference, "status": "SUCCESSFUL"},
                message=f"Webhook processed successfully for {provider}."
            )

        except Exception as e:
            logger.error(f"Webhook processing error for provider {provider}: {str(e)}")
            return ServiceResult.fail(f"Webhook processing exception: {str(e)}")
