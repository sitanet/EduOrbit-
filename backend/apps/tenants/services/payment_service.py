"""
Gateway-Agnostic Payment Processing Service for EduOrbit SaaS Platform.
Coordinates payment initialization, online gateway verification, manual payment processing, and workflow delegation.
"""

import logging
import uuid
from decimal import Decimal
from typing import Optional, Dict, Any
from django.db import transaction
from django.utils import timezone

from backend.apps.tenants.dto import ServiceResult
from backend.apps.tenants.exceptions import PaymentPolicyException, SubscriptionException
from backend.apps.tenants.models import SubscriptionInvoice, SubscriptionPayment, Tenant
from backend.apps.identity.models import User
from backend.apps.tenants.services.payment_gateway import PaymentGatewayFactory
from backend.apps.tenants.services.payment_policy import PaymentPolicyService
from backend.apps.tenants.services.subscription_workflow import SubscriptionWorkflowService
from backend.apps.tenants.services.audit_service import AuditService

logger = logging.getLogger(__name__)


class PaymentService:
    """
    High-level payment processor decoupled from specific gateway implementations.
    """

    @classmethod
    @transaction.atomic
    def initialize_payment(
        cls,
        invoice: SubscriptionInvoice,
        provider_name: str = "PAYSTACK",
        callback_url: Optional[str] = None,
        actor: Optional[User] = None
    ) -> ServiceResult:
        """
        Initializes online payment transaction for an invoice using the selected provider (PAYSTACK or OPAY).
        """
        try:
            # Step 1: Pre-condition validation
            policy_check = PaymentPolicyService.validate_invoice_payable(invoice=invoice)
            if not policy_check.success:
                return policy_check

            provider = str(provider_name).strip().upper()
            gateway = PaymentGatewayFactory.get_gateway(provider)

            # Step 2: Generate Reference
            short_ref = str(uuid.uuid4())[:8].upper()
            reference = f"{provider[:4]}-{invoice.invoice_number}-{short_ref}"

            # Step 3: Resolve Customer Email
            customer_email = "billing@eduorbit.com"
            if actor and hasattr(actor, 'email') and actor.email:
                customer_email = actor.email
            elif invoice.tenant:
                customer_email = f"admin@{invoice.tenant.name.lower().replace(' ', '')}.com"

            metadata = {
                "invoice_id": str(invoice.id),
                "invoice_number": invoice.invoice_number,
                "tenant_id": str(invoice.tenant_id),
                "invoice_type": invoice.invoice_type,
                "provider_name": provider
            }

            # Step 4: Call Gateway Initialization
            gw_result = gateway.initialize_transaction(
                amount=invoice.total_amount,
                reference=reference,
                customer_email=customer_email,
                callback_url=callback_url,
                metadata=metadata
            )

            if not gw_result.success:
                return gw_result

            # Step 5: Record INITIATED Payment Record
            payment, _ = SubscriptionPayment.objects.get_or_create(
                reference=reference,
                defaults={
                    'tenant': invoice.tenant,
                    'invoice': invoice,
                    'gateway': provider,
                    'payment_method': provider,
                    'amount': invoice.total_amount,
                    'status': 'INITIATED',
                    'paid_by': actor
                }
            )

            # Step 6: Log Audit Event
            AuditService.log_event(
                action="CREATED",
                tenant=invoice.tenant,
                invoice=invoice,
                payment=payment,
                actor=actor,
                notes=f"Payment transaction initialized with {provider}. Ref: {reference}"
            )

            logger.info(f"Initialized {provider} payment ref {reference} for invoice {invoice.invoice_number}")
            return ServiceResult.ok(
                data={
                    "payment_reference": reference,
                    "invoice_number": invoice.invoice_number,
                    "amount": float(invoice.total_amount),
                    "provider": provider,
                    "checkout_url": gw_result.data.get("checkout_url"),
                    "access_code": gw_result.data.get("access_code")
                },
                message=f"Payment initialized successfully with {provider}."
            )

        except Exception as e:
            logger.error(f"Failed to initialize payment for invoice {invoice.id}: {str(e)}")
            return ServiceResult.fail(f"Payment initialization failed: {str(e)}")

    @classmethod
    @transaction.atomic
    def verify_and_complete_payment(
        cls,
        payment_reference: str,
        provider_name: str = "PAYSTACK"
    ) -> ServiceResult:
        """
        Verifies transaction directly with gateway API and triggers workflow completion.
        """
        try:
            gateway = PaymentGatewayFactory.get_gateway(provider_name)
            ver_result = gateway.verify_transaction(reference=payment_reference)

            if not ver_result.success:
                return ver_result

            payment = SubscriptionPayment.objects.select_for_update().filter(reference=payment_reference).first()
            if not payment:
                return ServiceResult.fail(f"No payment record found for reference '{payment_reference}'.")

            invoice = payment.invoice
            if invoice.invoice_type == 'PARENT':
                return SubscriptionWorkflowService.complete_parent_payment_workflow(
                    invoice=invoice,
                    payment_reference=payment_reference,
                    payment_method=provider_name,
                    actor=payment.paid_by
                )
            else:
                return SubscriptionWorkflowService.complete_school_payment_workflow(
                    invoice=invoice,
                    payment_reference=payment_reference,
                    payment_method=provider_name,
                    actor=payment.paid_by
                )

        except Exception as e:
            logger.error(f"Failed to verify and complete payment ref {payment_reference}: {str(e)}")
            return ServiceResult.fail(f"Payment verification failed: {str(e)}")

    @classmethod
    @transaction.atomic
    def process_manual_payment(
        cls,
        invoice: SubscriptionInvoice,
        payment_method: str = "CASH",
        payment_reference: Optional[str] = None,
        actor: Optional[User] = None,
        paid_on_behalf: bool = True
    ) -> ServiceResult:
        """
        Processes offline/manual payments (CASH, POS, BANK_TRANSFER, CHEQUE) on behalf of parents or schools.
        """
        try:
            method = str(payment_method).upper()
            if method not in ['CASH', 'POS', 'BANK_TRANSFER', 'CHEQUE']:
                return ServiceResult.fail(f"Unsupported manual payment method: {payment_method}")

            ref = payment_reference or f"MANUAL-{method}-{invoice.invoice_number}-{str(uuid.uuid4())[:6].upper()}"

            if invoice.invoice_type == 'PARENT':
                return SubscriptionWorkflowService.complete_parent_payment_workflow(
                    invoice=invoice,
                    payment_reference=ref,
                    payment_method=method,
                    actor=actor,
                    paid_on_behalf=paid_on_behalf
                )
            else:
                return SubscriptionWorkflowService.complete_school_payment_workflow(
                    invoice=invoice,
                    payment_reference=ref,
                    payment_method=method,
                    actor=actor
                )

        except Exception as e:
            logger.error(f"Failed to process manual payment for invoice {invoice.id}: {str(e)}")
            return ServiceResult.fail(f"Manual payment processing failed: {str(e)}")
