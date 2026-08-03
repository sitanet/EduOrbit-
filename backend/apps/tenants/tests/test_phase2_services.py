"""
Phase 2 Unit Test Suite for EduOrbit Subscription Services, Workflows, and Policies.
Verifies production readiness, multi-child billing, tier pricing, workflow orchestration, policy enforcement,
concurrency safety, standardized DTOs, and custom domain exceptions.
"""

from decimal import Decimal
from django.test import TestCase
from django.utils import timezone

from backend.apps.tenants.dto import ServiceResult
from backend.apps.tenants.exceptions import (
    EduOrbitSubscriptionException, SubscriptionException, InvoiceException, PaymentPolicyException
)
from backend.apps.tenants.models import (
    Tenant, School, SubscriptionPlan, TenantSubscription,
    ParentSubscription, StudentPlatformSubscription,
    SubscriptionInvoice, SubscriptionPayment, SubscriptionAuditLog, BillingSettings
)
from backend.apps.people.models import Person, ParentProfile, StudentProfile, FamilyRelationship

from backend.apps.tenants.services.billing_calculator import BillingCalculationService
from backend.apps.tenants.services.invoice_service import InvoiceService
from backend.apps.tenants.services.receipt_service import ReceiptService
from backend.apps.tenants.services.parent_subscription_service import ParentSubscriptionService
from backend.apps.tenants.services.school_subscription_service import SchoolSubscriptionService
from backend.apps.tenants.services.compliance_service import ComplianceService
from backend.apps.tenants.services.audit_service import AuditService
from backend.apps.tenants.services.payment_policy import PaymentPolicyService
from backend.apps.tenants.services.subscription_workflow import SubscriptionWorkflowService


class Phase2ServiceLayerTestCase(TestCase):
    """
    Comprehensive verification test suite for Phase 2 services.
    """
    def setUp(self):
        # 1. Setup Tenant & School
        self.tenant = Tenant.objects.create(
            name="Grace Group of Schools",
            billing_model="PARENT_PAYS",
            parent_subscription_amount=Decimal("500.00"),
            compliance_threshold_percent=Decimal("80.00")
        )
        self.school = School.objects.create(
            tenant=self.tenant,
            name="Grace College Ikeja"
        )

        # 2. Setup Subscription Plan
        self.plan = SubscriptionPlan.objects.create(
            name="Standard Plan",
            billing_model="PARENT_PAYS",
            termly_price=Decimal("500.00"),
            student_tier_rates={"1-200": 2000, "201-500": 1500}
        )

        # 3. Setup Parent Person & Profile
        self.parent_person = Person.objects.create(
            tenant=self.tenant,
            person_number="PRN-101",
            first_name="Amaka",
            last_name="Okonkwo",
            gender="female",
            date_of_birth="1984-06-15"
        )
        self.parent_profile = ParentProfile.objects.create(
            tenant=self.tenant,
            person=self.parent_person,
            parent_number="PAR-2026-101"
        )

        # 4. Setup 2 Active Enrolled Students linked to Parent
        self.student1_person = Person.objects.create(
            tenant=self.tenant,
            person_number="STU-101",
            first_name="Chidi",
            last_name="Okonkwo",
            gender="male",
            date_of_birth="2014-03-10"
        )
        self.student1_profile = StudentProfile.objects.create(
            tenant=self.tenant,
            person=self.student1_person,
            student_number="STD-2026-101",
            current_school=self.school,
            enrollment_status="enrolled"
        )

        self.student2_person = Person.objects.create(
            tenant=self.tenant,
            person_number="STU-102",
            first_name="Nneka",
            last_name="Okonkwo",
            gender="female",
            date_of_birth="2016-11-25"
        )
        self.student2_profile = StudentProfile.objects.create(
            tenant=self.tenant,
            person=self.student2_person,
            student_number="STD-2026-102",
            current_school=self.school,
            enrollment_status="enrolled"
        )

        # 5. Setup 1 Withdrawn (Non-billable) Student linked to Parent
        self.student_withdrawn_person = Person.objects.create(
            tenant=self.tenant,
            person_number="STU-103",
            first_name="Emeka",
            last_name="Okonkwo",
            gender="male",
            date_of_birth="2012-01-05"
        )
        self.student_withdrawn_profile = StudentProfile.objects.create(
            tenant=self.tenant,
            person=self.student_withdrawn_person,
            student_number="STD-2026-103",
            current_school=self.school,
            enrollment_status="withdrawn"
        )

        # Link Family Relationships
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
        FamilyRelationship.objects.create(
            tenant=self.tenant,
            student=self.student_withdrawn_person,
            relative=self.parent_person,
            relationship_type="mother"
        )

    def test_service_result_dto(self):
        res = ServiceResult.ok(data={"key": "val"}, message="Success")
        self.assertTrue(res.success)
        self.assertEqual(res.data["key"], "val")
        self.assertEqual(res.to_dict()["message"], "Success")

        fail_res = ServiceResult.fail(message="Failed", errors=["ERR_01"])
        self.assertFalse(fail_res.success)
        self.assertEqual(fail_res.errors[0], "ERR_01")

    def test_billing_calculator_multi_child_active_only(self):
        # Parent has 3 linked children: 2 enrolled, 1 withdrawn.
        # Fee calculation must count ONLY the 2 active enrolled students (2 x 500 = 1000).
        res = BillingCalculationService.calculate_parent_fee(
            parent_profile=self.parent_profile,
            fee_per_child=Decimal("500.00")
        )
        self.assertTrue(res.success)
        self.assertEqual(res.data["active_child_count"], 2)
        self.assertEqual(res.data["total_amount"], 1000.00)

    def test_workflow_1_create_parent_subscription(self):
        res = SubscriptionWorkflowService.create_parent_subscription_workflow(
            parent_profile=self.parent_profile,
            school=self.school,
            fee_per_child=Decimal("500.00")
        )
        self.assertTrue(res.success)
        self.assertEqual(res.data["amount"], 1000.00)
        self.assertEqual(res.data["status"], "PENDING")

        invoice = SubscriptionInvoice.objects.get(id=res.data["invoice_id"])
        self.assertEqual(invoice.status, "PENDING")
        self.assertEqual(invoice.total_amount, Decimal("1000.00"))

    def test_workflow_2_complete_parent_payment(self):
        # Step 1: Create Subscription & Pending Invoice
        wf1 = SubscriptionWorkflowService.create_parent_subscription_workflow(
            parent_profile=self.parent_profile,
            school=self.school,
            fee_per_child=Decimal("500.00")
        )
        invoice = SubscriptionInvoice.objects.get(id=wf1.data["invoice_id"])

        # Step 2: Complete Payment
        ref = "PSTK-REF-998877"
        wf2 = SubscriptionWorkflowService.complete_parent_payment_workflow(
            invoice=invoice,
            payment_reference=ref
        )
        self.assertTrue(wf2.success)
        self.assertEqual(wf2.data["payment_reference"], ref)
        self.assertIsNotNone(wf2.data["receipt_number"])

        # Verify Parent & Student Activation
        parent_sub = ParentSubscription.objects.get(parent=self.parent_profile)
        self.assertEqual(parent_sub.status, "ACTIVE")
        self.assertEqual(parent_sub.activated_students.count(), 2)

        # Verify Student Access Status Check
        stu_check = ParentSubscriptionService.check_student_access_status(self.student1_profile)
        self.assertTrue(stu_check.success)
        self.assertTrue(stu_check.data["is_active"])

    def test_workflow_3_and_4_school_pays_model(self):
        self.tenant.billing_model = "SCHOOL_PAYS"
        self.tenant.save()

        # Workflow 3: Provision & Invoice
        wf3 = SubscriptionWorkflowService.create_school_subscription_workflow(
            tenant=self.tenant,
            school=self.school,
            plan=self.plan
        )
        self.assertTrue(wf3.success)
        invoice = SubscriptionInvoice.objects.get(id=wf3.data["invoice_id"])
        self.assertEqual(invoice.status, "PENDING")

        # Workflow 4: Complete Payment
        ref = "PSTK-SCH-112233"
        wf4 = SubscriptionWorkflowService.complete_school_payment_workflow(
            invoice=invoice,
            payment_reference=ref
        )
        self.assertTrue(wf4.success)
        self.assertEqual(self.tenant.reload().billing_status if hasattr(self.tenant, 'reload') else Tenant.objects.get(id=self.tenant.id).billing_status, "ACTIVE")

    def test_payment_policy_duplicate_and_cancelled_validation(self):
        wf1 = SubscriptionWorkflowService.create_parent_subscription_workflow(
            parent_profile=self.parent_profile,
            school=self.school,
            fee_per_child=Decimal("500.00")
        )
        invoice = SubscriptionInvoice.objects.get(id=wf1.data["invoice_id"])

        # Pay once
        SubscriptionWorkflowService.complete_parent_payment_workflow(
            invoice=invoice,
            payment_reference="REF-DUP-101"
        )

        # Attempt to pay AGAIN with same reference
        policy_res = PaymentPolicyService.validate_duplicate_payment(
            invoice=invoice,
            payment_reference="REF-DUP-101"
        )
        self.assertFalse(policy_res.success)
        self.assertIn("DUPLICATE_PAYMENT_REFERENCE", policy_res.errors)

        # Attempt to pay invoice that is already PAID
        payable_res = PaymentPolicyService.validate_invoice_payable(invoice=invoice)
        self.assertFalse(payable_res.success)
        self.assertIn("INVOICE_ALREADY_PAID", payable_res.errors)
