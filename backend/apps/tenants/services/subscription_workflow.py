"""
Subscription Workflow Orchestrator for EduOrbit SaaS Platform.
Coordinates complete end-to-end subscription workflows by delegating to specialized domain services.
THIS SERVICE CONTAINS ORCHESTRATION ONLY. NO calculations, validation, or pricing logic live here.
"""

import logging
from decimal import Decimal
from typing import Optional, Dict, Any
from django.db import transaction
from django.utils import timezone

from backend.apps.tenants.dto import ServiceResult
from backend.apps.tenants.exceptions import EduOrbitSubscriptionException, ValidationException
from backend.apps.tenants.models import (
    Tenant, School, SubscriptionPlan, ParentSubscription, TenantSubscription, SubscriptionInvoice, SubscriptionPayment
)
from backend.apps.people.models import ParentProfile
from backend.apps.academic.models import AcademicPeriod
from backend.apps.identity.models import User

from backend.apps.tenants.services.billing_calculator import BillingCalculationService
from backend.apps.tenants.services.parent_subscription_service import ParentSubscriptionService
from backend.apps.tenants.services.school_subscription_service import SchoolSubscriptionService
from backend.apps.tenants.services.invoice_service import InvoiceService
from backend.apps.tenants.services.receipt_service import ReceiptService
from backend.apps.tenants.services.payment_policy import PaymentPolicyService
from backend.apps.tenants.services.compliance_service import ComplianceService
from backend.apps.tenants.services.audit_service import AuditService

logger = logging.getLogger(__name__)


class SubscriptionWorkflowService:
    """
    Workflow Orchestration Engine coordinating subscription creation, payment completion,
    activation, and audit logging.
    """

    # ==============================================================
    # WORKFLOW 1: CREATE PARENT SUBSCRIPTION
    # ==============================================================
    @classmethod
    @transaction.atomic
    def create_parent_subscription_workflow(
        cls,
        parent_profile: ParentProfile,
        school: School,
        academic_period: Optional[AcademicPeriod] = None,
        fee_per_child: Decimal = Decimal("5000.00"),
        actor: Optional[User] = None
    ) -> ServiceResult:
        """
        Workflow 1: Create Parent Subscription & Pending Invoice
        Steps:
        1. BillingCalculationService.calculate_parent_fee()
        2. ParentSubscriptionService.create_or_get_parent_subscription()
        3. InvoiceService.create_parent_invoice()
        4. AuditService.log_event()
        STOP (Invoice remains pending).
        """
        logger.info(f"Starting Workflow 1: Create Parent Subscription for {parent_profile.parent_number}")
        try:
            tenant = parent_profile.tenant

            # Step 1: Calculate Fee
            calc_result = BillingCalculationService.calculate_parent_fee(
                parent_profile=parent_profile,
                fee_per_child=fee_per_child
            )
            if not calc_result.success:
                return calc_result

            calc_amount = Decimal(str(calc_result.data.get("total_amount", 0.00)))

            # Step 2: Initialize ParentSubscription Record
            parent_sub_result = ParentSubscriptionService.create_or_get_parent_subscription(
                parent_profile=parent_profile,
                academic_period=academic_period,
                fee_per_child=fee_per_child
            )
            if not parent_sub_result.success:
                return parent_sub_result

            sub_id = parent_sub_result.data.get("parent_subscription_id")
            parent_sub = ParentSubscription.objects.get(id=sub_id)

            # Step 3: Generate Pending Invoice
            inv_result = InvoiceService.create_parent_invoice(
                tenant=tenant,
                school=school,
                parent_subscription=parent_sub,
                amount=calc_amount
            )
            if not inv_result.success:
                return inv_result

            inv_id = inv_result.data.get("invoice_id")
            invoice = SubscriptionInvoice.objects.get(id=inv_id)

            # Step 4: Audit Log Event
            AuditService.log_event(
                action="CREATED",
                tenant=tenant,
                parent_subscription=parent_sub,
                invoice=invoice,
                actor=actor,
                notes=f"Parent Subscription & Pending Invoice {invoice.invoice_number} created for {parent_profile.parent_number}."
            )

            logger.info(f"Workflow 1 Completed: Invoice {invoice.invoice_number} generated for {parent_profile.parent_number}")
            return ServiceResult.ok(
                data={
                    "parent_subscription_id": str(parent_sub.id),
                    "invoice_id": str(invoice.id),
                    "invoice_number": invoice.invoice_number,
                    "amount": float(calc_amount),
                    "status": "PENDING"
                },
                message="Parent subscription invoice generated successfully and is pending payment."
            )

        except Exception as e:
            logger.error(f"Workflow 1 Failed for parent {parent_profile.id}: {str(e)}")
            return ServiceResult.fail(f"Workflow failed: {str(e)}")

    # ==============================================================
    # WORKFLOW 2: COMPLETE PARENT PAYMENT
    # ==============================================================
    @classmethod
    @transaction.atomic
    def complete_parent_payment_workflow(
        cls,
        invoice: SubscriptionInvoice,
        payment_reference: str,
        payment_method: str = "PAYSTACK",
        actor: Optional[User] = None,
        paid_on_behalf: bool = False
    ) -> ServiceResult:
        """
        Workflow 2: Complete Parent Subscription Payment
        Steps:
        1. PaymentPolicyService.validate_invoice_payable() & validate_duplicate_payment()
        2. (Actual payment processing verified upstream / Phase 3)
        3. InvoiceService.mark_invoice_paid()
        4. SubscriptionPayment record created & ReceiptService.create_receipt()
        5. ParentSubscriptionService.activate_parent_subscription() [Activates ALL linked active children]
        6. ComplianceService.calculate_school_compliance_metrics()
        7. AuditService.log_event()
        """
        logger.info(f"Starting Workflow 2: Complete Parent Payment for Invoice {invoice.invoice_number}")
        try:
            tenant = invoice.tenant

            # Step 1: Payment Policy Pre-Condition Validations
            policy_check = PaymentPolicyService.validate_invoice_payable(invoice=invoice)
            if not policy_check.success:
                return policy_check

            dup_check = PaymentPolicyService.validate_duplicate_payment(
                invoice=invoice,
                payment_reference=payment_reference
            )
            if not dup_check.success:
                return dup_check

            # Step 3: Mark Invoice Paid
            paid_inv_result = InvoiceService.mark_invoice_paid(invoice=invoice)
            if not paid_inv_result.success:
                return paid_inv_result

            # Step 4: Create SubscriptionPayment Record & Generate Receipt
            payment = SubscriptionPayment.objects.create(
                tenant=tenant,
                reference=payment_reference,
                invoice=invoice,
                gateway="Paystack" if payment_method == "PAYSTACK" else "Manual",
                payment_method=payment_method,
                amount=invoice.total_amount,
                status="SUCCESSFUL",
                paid_by=actor,
                paid_on_behalf=paid_on_behalf,
                paid_at=timezone.now()
            )

            receipt_result = ReceiptService.create_receipt(payment=payment, invoice=invoice)
            if not receipt_result.success:
                return receipt_result

            # Step 5: Activate Parent Subscription & ALL Linked Active Children
            parent_sub = invoice.parent_subscriptions.first()
            if parent_sub:
                act_result = ParentSubscriptionService.activate_parent_subscription(
                    parent_subscription=parent_sub
                )
                if not act_result.success:
                    return act_result

            # Step 6: Recalculate School Compliance Metrics
            comp_result = ComplianceService.calculate_school_compliance_metrics(tenant=tenant)

            # Step 7: Record Audit Log
            AuditService.log_event(
                action="PAYMENT",
                tenant=tenant,
                parent_subscription=parent_sub,
                invoice=invoice,
                payment=payment,
                actor=actor,
                notes=f"Parent Payment {payment_reference} completed for invoice {invoice.invoice_number}. Access activated."
            )

            logger.info(f"Workflow 2 Completed successfully for Invoice {invoice.invoice_number}")
            return ServiceResult.ok(
                data={
                    "invoice_number": invoice.invoice_number,
                    "payment_reference": payment_reference,
                    "receipt_number": payment.receipt_number,
                    "compliance_metrics": comp_result.data if comp_result.success else {}
                },
                message="Parent payment completed successfully and accounts activated."
            )

        except Exception as e:
            logger.error(f"Workflow 2 Failed for invoice {invoice.id}: {str(e)}")
            return ServiceResult.fail(f"Parent payment workflow failed: {str(e)}")

    # ==============================================================
    # WORKFLOW 3: CREATE SCHOOL SUBSCRIPTION
    # ==============================================================
    @classmethod
    @transaction.atomic
    def create_school_subscription_workflow(
        cls,
        tenant: Tenant,
        school: School,
        plan: SubscriptionPlan,
        actor: Optional[User] = None
    ) -> ServiceResult:
        """
        Workflow 3: Create School Subscription & Pending Invoice (SCHOOL_PAYS Model)
        Steps:
        1. BillingCalculationService.calculate_school_fee()
        2. SchoolSubscriptionService.calculate_and_provision_school_subscription()
        3. InvoiceService.create_school_invoice()
        4. AuditService.log_event()
        STOP (Invoice remains pending).
        """
        logger.info(f"Starting Workflow 3: Create School Subscription for {tenant.name}")
        try:
            # Step 1 & 2: Provision School Subscription & Compute Fee
            prov_result = SchoolSubscriptionService.calculate_and_provision_school_subscription(
                tenant=tenant,
                plan=plan
            )
            if not prov_result.success:
                return prov_result

            sub_id = prov_result.data.get("subscription_id")
            tenant_sub = TenantSubscription.objects.get(id=sub_id)
            calc_amount = Decimal(str(prov_result.data.get("calculated_amount", 0.00)))

            # Step 3: Generate Pending School Invoice
            inv_result = InvoiceService.create_school_invoice(
                tenant=tenant,
                school=school,
                tenant_subscription=tenant_sub,
                amount=calc_amount
            )
            if not inv_result.success:
                return inv_result

            inv_id = inv_result.data.get("invoice_id")
            invoice = SubscriptionInvoice.objects.get(id=inv_id)

            # Step 4: Record Audit Log
            AuditService.log_event(
                action="CREATED",
                tenant=tenant,
                tenant_subscription=tenant_sub,
                invoice=invoice,
                actor=actor,
                notes=f"School Subscription & Pending Invoice {invoice.invoice_number} created for {tenant.name}."
            )

            logger.info(f"Workflow 3 Completed: School Invoice {invoice.invoice_number} created for {tenant.name}")
            return ServiceResult.ok(
                data={
                    "tenant_subscription_id": str(tenant_sub.id),
                    "invoice_id": str(invoice.id),
                    "invoice_number": invoice.invoice_number,
                    "amount": float(calc_amount),
                    "status": "PENDING"
                },
                message="School subscription invoice generated successfully and is pending payment."
            )

        except Exception as e:
            logger.error(f"Workflow 3 Failed for tenant {tenant.id}: {str(e)}")
            return ServiceResult.fail(f"School subscription workflow failed: {str(e)}")

    # ==============================================================
    # WORKFLOW 4: COMPLETE SCHOOL PAYMENT
    # ==============================================================
    @classmethod
    @transaction.atomic
    def complete_school_payment_workflow(
        cls,
        invoice: SubscriptionInvoice,
        payment_reference: str,
        payment_method: str = "PAYSTACK",
        actor: Optional[User] = None
    ) -> ServiceResult:
        """
        Workflow 4: Complete School Subscription Payment
        Steps:
        1. PaymentPolicyService.validate_invoice_payable() & validate_duplicate_payment()
        2. InvoiceService.mark_invoice_paid()
        3. SubscriptionPayment & ReceiptService.create_receipt()
        4. SchoolSubscriptionService.activate_school_parent_access() [Activates platform-wide access]
        5. ComplianceService.calculate_school_compliance_metrics()
        6. AuditService.log_event()
        """
        logger.info(f"Starting Workflow 4: Complete School Payment for Invoice {invoice.invoice_number}")
        try:
            tenant = invoice.tenant

            # Step 1: Policy Validation
            policy_check = PaymentPolicyService.validate_invoice_payable(invoice=invoice)
            if not policy_check.success:
                return policy_check

            dup_check = PaymentPolicyService.validate_duplicate_payment(
                invoice=invoice,
                payment_reference=payment_reference
            )
            if not dup_check.success:
                return dup_check

            # Step 2: Mark Invoice Paid
            paid_inv_result = InvoiceService.mark_invoice_paid(invoice=invoice)
            if not paid_inv_result.success:
                return paid_inv_result

            # Step 3: Payment Record & Receipt
            payment = SubscriptionPayment.objects.create(
                tenant=tenant,
                reference=payment_reference,
                invoice=invoice,
                gateway="Paystack" if payment_method == "PAYSTACK" else "Manual",
                payment_method=payment_method,
                amount=invoice.total_amount,
                status="SUCCESSFUL",
                paid_by=actor,
                paid_at=timezone.now()
            )

            receipt_result = ReceiptService.create_receipt(payment=payment, invoice=invoice)
            if not receipt_result.success:
                return receipt_result

            # Step 4: Activate Platform-Wide Access
            tenant_sub = invoice.tenant_subscription
            if tenant_sub:
                act_result = SchoolSubscriptionService.activate_school_parent_access(
                    tenant_subscription=tenant_sub
                )
                if not act_result.success:
                    return act_result

            # Step 5: Recalculate Compliance
            comp_result = ComplianceService.calculate_school_compliance_metrics(tenant=tenant)

            # Step 6: Record Audit Log
            AuditService.log_event(
                action="PAYMENT",
                tenant=tenant,
                tenant_subscription=tenant_sub,
                invoice=invoice,
                payment=payment,
                actor=actor,
                notes=f"School Payment {payment_reference} completed for invoice {invoice.invoice_number}. Platform-wide access activated."
            )

            logger.info(f"Workflow 4 Completed successfully for School Invoice {invoice.invoice_number}")
            return ServiceResult.ok(
                data={
                    "invoice_number": invoice.invoice_number,
                    "payment_reference": payment_reference,
                    "receipt_number": payment.receipt_number,
                    "compliance_metrics": comp_result.data if comp_result.success else {}
                },
                message="School subscription payment completed successfully."
            )

        except Exception as e:
            logger.error(f"Workflow 4 Failed for invoice {invoice.id}: {str(e)}")
            return ServiceResult.fail(f"School payment workflow failed: {str(e)}")
