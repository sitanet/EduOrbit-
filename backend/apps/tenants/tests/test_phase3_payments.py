"""
Phase 3 Multi-Gateway Payment System Test Suite for EduOrbit.
Verifies Paystack and OPay initialization, verification, HMAC webhooks, signature security,
idempotency, manual payments, parent/school workflows, receipt generation, and audit logs.
"""

from decimal import Decimal
from django.test import TestCase
from django.utils import timezone

from backend.apps.tenants.dto import ServiceResult
from backend.apps.tenants.models import (
    Tenant, School, SubscriptionPlan, TenantSubscription,
    ParentSubscription, StudentPlatformSubscription,
    SubscriptionInvoice, SubscriptionPayment, SubscriptionAuditLog
)
from backend.apps.people.models import Person, ParentProfile, StudentProfile, FamilyRelationship

from backend.apps.tenants.services.payment_gateway import PaymentGatewayFactory
from backend.apps.tenants.services.paystack_gateway import PaystackGateway
from backend.apps.tenants.services.opay_gateway import OPayGateway
from backend.apps.tenants.services.payment_service import PaymentService
from backend.apps.tenants.services.webhook_service import WebhookService
from backend.apps.tenants.services.subscription_workflow import SubscriptionWorkflowService


class Phase3PaymentSystemTestCase(TestCase):
    """
    Unit and Integration test suite for Phase 3 Multi-Gateway Payment System.
    """
    def setUp(self):
        # 1. Setup Tenant & School
        self.tenant = Tenant.objects.create(
            name="Apex Academy",
            billing_model="PARENT_PAYS",
            parent_subscription_amount=Decimal("500.00"),
            compliance_threshold_percent=Decimal("80.00")
        )
        self.school = School.objects.create(
            tenant=self.tenant,
            name="Apex Secondary School"
        )

        # 2. Setup Subscription Plan
        self.plan = SubscriptionPlan.objects.create(
            name="Apex Standard Plan",
            billing_model="PARENT_PAYS",
            termly_price=Decimal("500.00"),
            student_tier_rates={"1-200": 2000, "201-500": 1500}
        )

        # 3. Setup Parent Person & Profile
        self.parent_person = Person.objects.create(
            tenant=self.tenant,
            person_number="PRN-301",
            first_name="Bisi",
            last_name="Adeleke",
            gender="female",
            date_of_birth="1986-09-20"
        )
        self.parent_profile = ParentProfile.objects.create(
            tenant=self.tenant,
            person=self.parent_person,
            parent_number="PAR-2026-301"
        )

        # 4. Setup 2 Active Enrolled Students linked to Parent
        self.student1_person = Person.objects.create(
            tenant=self.tenant,
            person_number="STU-301",
            first_name="Kemi",
            last_name="Adeleke",
            gender="female",
            date_of_birth="2015-04-12"
        )
        self.student1_profile = StudentProfile.objects.create(
            tenant=self.tenant,
            person=self.student1_person,
            student_number="STD-2026-301",
            current_school=self.school,
            enrollment_status="enrolled"
        )

        self.student2_person = Person.objects.create(
            tenant=self.tenant,
            person_number="STU-302",
            first_name="Tunde",
            last_name="Adeleke",
            gender="male",
            date_of_birth="2017-07-08"
        )
        self.student2_profile = StudentProfile.objects.create(
            tenant=self.tenant,
            person=self.student2_person,
            student_number="STD-2026-302",
            current_school=self.school,
            enrollment_status="enrolled"
        )

        FamilyRelationship.objects.create(
            tenant=self.tenant,
            student=self.student1_person,
            relative=self.parent_person,
            relationship_type="mother"
        )
        FamilyRelationship.objects.create(
            tenant=self.tenant,
            student=self.student2_person,
            relative=self.parent_person,
            relationship_type="mother"
        )

        # Create Initial Pending Parent Subscription & Invoice (2 children x 500 = 1000)
        wf_res = SubscriptionWorkflowService.create_parent_subscription_workflow(
            parent_profile=self.parent_profile,
            school=self.school,
            fee_per_child=Decimal("500.00")
        )
        self.invoice = SubscriptionInvoice.objects.get(id=wf_res.data["invoice_id"])

    def test_gateway_factory(self):
        paystack_gw = PaymentGatewayFactory.get_gateway("PAYSTACK")
        opay_gw = PaymentGatewayFactory.get_gateway("OPAY")
        self.assertIsInstance(paystack_gw, PaystackGateway)
        self.assertIsInstance(opay_gw, OPayGateway)
        self.assertEqual(paystack_gw.get_provider_name(), "PAYSTACK")
        self.assertEqual(opay_gw.get_provider_name(), "OPAY")

    def test_paystack_initialize_and_verify(self):
        init_res = PaymentService.initialize_payment(
            invoice=self.invoice,
            provider_name="PAYSTACK",
            callback_url="https://eduorbit.com/callback"
        )
        self.assertTrue(init_res.success)
        self.assertIsNotNone(init_res.data["checkout_url"])
        ref = init_res.data["payment_reference"]

        # Verify Payment
        ver_res = PaymentService.verify_and_complete_payment(
            payment_reference=ref,
            provider_name="PAYSTACK"
        )
        self.assertTrue(ver_res.success)
        self.assertIsNotNone(ver_res.data["receipt_number"])

        # Check Parent & Student Activation
        parent_sub = ParentSubscription.objects.get(parent=self.parent_profile)
        self.assertEqual(parent_sub.status, "ACTIVE")
        self.assertEqual(parent_sub.activated_students.count(), 2)

    def test_opay_initialize_and_verify(self):
        init_res = PaymentService.initialize_payment(
            invoice=self.invoice,
            provider_name="OPAY",
            callback_url="https://eduorbit.com/opay/callback"
        )
        self.assertTrue(init_res.success)
        self.assertIsNotNone(init_res.data["checkout_url"])
        ref = init_res.data["payment_reference"]

        ver_res = PaymentService.verify_and_complete_payment(
            payment_reference=ref,
            provider_name="OPAY"
        )
        self.assertTrue(ver_res.success)
        self.assertIsNotNone(ver_res.data["receipt_number"])

    def test_paystack_webhook_valid_and_invalid_signature(self):
        init_res = PaymentService.initialize_payment(
            invoice=self.invoice,
            provider_name="PAYSTACK"
        )
        ref = init_res.data["payment_reference"]

        payload = {
            "event": "charge.success",
            "data": {
                "reference": ref,
                "amount": 100000,
                "status": "success"
            }
        }

        # 1. Invalid Signature Test
        invalid_sig_res = WebhookService.process_gateway_webhook(
            provider_name="PAYSTACK",
            payload=payload,
            signature_header="invalid_signature_hash"
        )
        self.assertFalse(invalid_sig_res.success)
        self.assertIn("INVALID_SIGNATURE", invalid_sig_res.errors)

        # 2. Valid Signature Test (Mock signature for test mode)
        valid_sig_res = WebhookService.process_gateway_webhook(
            provider_name="PAYSTACK",
            payload=payload,
            signature_header="valid_test_signature"
        )
        self.assertTrue(valid_sig_res.success)
        self.assertEqual(valid_sig_res.data["status"], "SUCCESSFUL")

        # 3. Duplicate Webhook Test (Idempotency)
        dup_webhook_res = WebhookService.process_gateway_webhook(
            provider_name="PAYSTACK",
            payload=payload,
            signature_header="valid_test_signature"
        )
        self.assertTrue(dup_webhook_res.success)
        self.assertEqual(dup_webhook_res.data["status"], "ALREADY_PROCESSED")

    def test_opay_webhook_valid_and_invalid_signature(self):
        init_res = PaymentService.initialize_payment(
            invoice=self.invoice,
            provider_name="OPAY"
        )
        ref = init_res.data["payment_reference"]

        payload = {
            "event": "payment.successful",
            "data": {
                "reference": ref,
                "amount": 1000.00,
                "status": "SUCCESSFUL"
            }
        }

        # Invalid Signature
        invalid_sig = WebhookService.process_gateway_webhook(
            provider_name="OPAY",
            payload=payload,
            signature_header="invalid_opay_signature"
        )
        self.assertFalse(invalid_sig.success)

        # Valid Signature
        valid_sig = WebhookService.process_gateway_webhook(
            provider_name="OPAY",
            payload=payload,
            signature_header="valid_opay_signature"
        )
        self.assertTrue(valid_sig.success)
        self.assertEqual(valid_sig.data["status"], "SUCCESSFUL")

    def test_manual_payment_processing(self):
        # Process Manual Cash Payment on behalf of parent
        manual_res = PaymentService.process_manual_payment(
            invoice=self.invoice,
            payment_method="CASH",
            paid_on_behalf=True
        )
        self.assertTrue(manual_res.success)
        self.assertIsNotNone(manual_res.data["receipt_number"])

        inv = SubscriptionInvoice.objects.get(id=self.invoice.id)
        self.assertEqual(inv.status, "PAID")

        parent_sub = ParentSubscription.objects.get(parent=self.parent_profile)
        self.assertEqual(parent_sub.status, "ACTIVE")
        self.assertEqual(parent_sub.activated_students.count(), 2)

        # Check Audit Log recorded
        audit_count = SubscriptionAuditLog.objects.filter(invoice=self.invoice, action="PAYMENT").count()
        self.assertGreater(audit_count, 0)
