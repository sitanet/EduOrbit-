from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from backend.apps.tenants.models import (
    Tenant, School, SubscriptionPlan, TenantSubscription,
    ParentSubscription, StudentPlatformSubscription,
    SubscriptionInvoice, SubscriptionPayment, SubscriptionAuditLog, BillingSettings
)
from backend.apps.people.models import Person, ParentProfile, StudentProfile, FamilyRelationship

class Phase1DatabaseFoundationTestCase(TestCase):
    """
    Phase 1 Verification Tests for EduOrbit Parent & Student Access Subscription Schema.
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
            name="Standard Parent & Student Access Plan",
            billing_model="PARENT_PAYS",
            termly_price=Decimal("500.00"),
            student_tier_rates={"1-200": 2000, "201-500": 1500}
        )

        # 3. Setup Parent Person & Profile
        self.parent_person = Person.objects.create(
            tenant=self.tenant,
            person_number="PRN-001",
            first_name="Amaka",
            last_name="Johnson",
            gender="female",
            date_of_birth="1985-05-12"
        )
        self.parent_profile = ParentProfile.objects.create(
            tenant=self.tenant,
            person=self.parent_person,
            parent_number="PAR-2026-001"
        )

        # 4. Setup 2 Student Persons & Profiles linked to same Parent
        self.student1_person = Person.objects.create(
            tenant=self.tenant,
            person_number="STU-001",
            first_name="David",
            last_name="Johnson",
            gender="male",
            date_of_birth="2015-08-20"
        )
        self.student1_profile = StudentProfile.objects.create(
            tenant=self.tenant,
            person=self.student1_person,
            student_number="STD-2026-101",
            current_school=self.school
        )

        self.student2_person = Person.objects.create(
            tenant=self.tenant,
            person_number="STU-002",
            first_name="Sarah",
            last_name="Johnson",
            gender="female",
            date_of_birth="2017-02-14"
        )
        self.student2_profile = StudentProfile.objects.create(
            tenant=self.tenant,
            person=self.student2_person,
            student_number="STD-2026-102",
            current_school=self.school
        )

        # Link Family Relationships
        FamilyRelationship.objects.create(
            tenant=self.tenant,
            student=self.student1_person,
            relative=self.parent_person,
            relationship_type="mother",
            legal_guardian=True
        )
        FamilyRelationship.objects.create(
            tenant=self.tenant,
            student=self.student2_person,
            relative=self.parent_person,
            relationship_type="mother",
            legal_guardian=True
        )

    def test_parent_subscription_multi_child_sum_calculation(self):
        # 2 Children @ 500 per child -> 1000 total amount
        parent_sub = ParentSubscription.objects.create(
            tenant=self.tenant,
            parent=self.parent_profile,
            child_count=2,
            fee_per_child=Decimal("500.00"),
            status="ACTIVE",
            paid_until=timezone.now() + timezone.timedelta(days=120)
        )

        self.assertEqual(parent_sub.amount, Decimal("1000.00"))

    def test_single_parent_subscription_activates_multiple_students(self):
        parent_sub = ParentSubscription.objects.create(
            tenant=self.tenant,
            parent=self.parent_profile,
            child_count=2,
            fee_per_child=Decimal("500.00"),
            status="ACTIVE",
            paid_until=timezone.now() + timezone.timedelta(days=120)
        )

        student1_sub = StudentPlatformSubscription.objects.create(
            tenant=self.tenant,
            student=self.student1_profile,
            parent_subscription=parent_sub,
            amount=Decimal("0.00"),
            payment_status="ACTIVE"
        )
        student2_sub = StudentPlatformSubscription.objects.create(
            tenant=self.tenant,
            student=self.student2_profile,
            parent_subscription=parent_sub,
            amount=Decimal("0.00"),
            payment_status="ACTIVE"
        )

        self.assertEqual(parent_sub.amount, Decimal("1000.00"))
        self.assertEqual(parent_sub.activated_students.count(), 2)
        self.assertEqual(student1_sub.parent_subscription, parent_sub)
        self.assertEqual(student2_sub.parent_subscription, parent_sub)

    def test_payment_and_audit_logging_models(self):
        invoice = SubscriptionInvoice.objects.create(
            tenant=self.tenant,
            invoice_number="INV-2026-0002",
            invoice_type="PARENT",
            school=self.school,
            amount=Decimal("1000.00"),
            tax_amount=Decimal("0.00"),
            total_amount=Decimal("1000.00"),
            due_date=timezone.now()
        )

        payment = SubscriptionPayment.objects.create(
            tenant=self.tenant,
            reference="PSTK-TEST-998877",
            invoice=invoice,
            gateway="Paystack",
            payment_method="PAYSTACK",
            amount=Decimal("1000.00"),
            status="SUCCESSFUL",
            receipt_number="REC-2026-0001",
            paid_at=timezone.now()
        )

        audit = SubscriptionAuditLog.objects.create(
            tenant=self.tenant,
            action="PAYMENT",
            invoice=invoice,
            payment=payment,
            notes="Paystack payment processed successfully for Parent PRN-001"
        )

        self.assertEqual(payment.status, "SUCCESSFUL")
        self.assertEqual(audit.action, "PAYMENT")

    def test_billing_settings_singleton(self):
        settings = BillingSettings.objects.create(
            reminder_schedule_days=[30, 14, 7, 3, 1, 0],
            grace_period_days_default=7,
            currency="NGN",
            invoice_prefix="INV-",
            receipt_prefix="REC-"
        )
        self.assertEqual(settings.currency, "NGN")
        self.assertIn(30, settings.reminder_schedule_days)
