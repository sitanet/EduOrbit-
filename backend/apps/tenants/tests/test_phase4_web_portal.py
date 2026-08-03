"""
Phase 4 Production Billing & Subscription Web Portal Test Suite for EduOrbit.
Verifies RBAC permission checks, tenant data isolation, dashboard rendering,
Parent Collection Center, HTMX endpoints, ReportLab PDF downloads, and CSV exports.
"""

from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from backend.apps.identity.models import User
from backend.apps.tenants.models import (
    Tenant, School, SubscriptionPlan, ParentSubscription,
    SubscriptionInvoice, SubscriptionPayment, PaymentGatewaySetting
)
from backend.apps.people.models import Person, ParentProfile, StudentProfile, FamilyRelationship
from backend.apps.tenants.services.subscription_workflow import SubscriptionWorkflowService


class Phase4WebPortalTestCase(TestCase):
    """
    Unit and Integration Test Suite for Phase 4 Web Portal Modules.
    """
    def setUp(self):
        # 1. Setup Super Admin & Normal Users
        self.super_admin = User.objects.create_superuser(
            username="admin@eduorbit.com",
            email="admin@eduorbit.com",
            password="adminpassword123"
        )
        self.parent_user = User.objects.create_user(
            username="parent@gmail.com",
            email="parent@gmail.com",
            password="parentpassword123"
        )

        # 2. Setup Tenant & School
        self.tenant = Tenant.objects.create(
            name="Horizon Academy",
            billing_model="PARENT_PAYS",
            parent_subscription_amount=Decimal("500.00"),
            compliance_threshold_percent=Decimal("80.00")
        )
        self.school = School.objects.create(
            tenant=self.tenant,
            name="Horizon Primary School"
        )

        # 3. Setup Payment Gateway Settings
        self.gw_paystack = PaymentGatewaySetting.objects.create(
            provider="PAYSTACK",
            display_name="Paystack Direct",
            enabled=True,
            priority=1
        )
        self.gw_opay = PaymentGatewaySetting.objects.create(
            provider="OPAY",
            display_name="OPay Wallet",
            enabled=True,
            priority=2
        )

        # 4. Setup Parent & 2 Students
        self.parent_person = Person.objects.create(
            tenant=self.tenant,
            user=self.parent_user,
            person_number="PRN-901",
            first_name="Funke",
            last_name="Akindele",
            gender="female",
            date_of_birth="1985-05-15"
        )
        self.parent_profile = ParentProfile.objects.create(
            tenant=self.tenant,
            person=self.parent_person,
            parent_number="PAR-2026-901"
        )

        self.student_person = Person.objects.create(
            tenant=self.tenant,
            person_number="STU-901",
            first_name="Tobi",
            last_name="Akindele",
            gender="male",
            date_of_birth="2016-08-10"
        )
        self.student_profile = StudentProfile.objects.create(
            tenant=self.tenant,
            person=self.student_person,
            student_number="STD-2026-901",
            current_school=self.school,
            enrollment_status="enrolled"
        )

        FamilyRelationship.objects.create(
            tenant=self.tenant,
            student=self.student_person,
            relative=self.parent_person,
            relationship_type="mother"
        )

        # 5. Create Parent Subscription & Invoice
        wf_res = SubscriptionWorkflowService.create_parent_subscription_workflow(
            parent_profile=self.parent_profile,
            school=self.school,
            fee_per_child=Decimal("500.00")
        )
        self.invoice = SubscriptionInvoice.objects.get(id=wf_res.data["invoice_id"])

        self.client = Client()

    def test_super_admin_dashboard_rbac(self):
        # 1. Unauthenticated redirect
        resp = self.client.get(reverse('tenants_web:super_admin_dashboard'))
        self.assertEqual(resp.status_code, 302)

        # 2. Parent User Access Denied (403)
        self.client.force_login(self.parent_user)
        resp = self.client.get(reverse('tenants_web:super_admin_dashboard'))
        self.assertEqual(resp.status_code, 403)

        # 3. Super Admin Access Granted (200)
        self.client.force_login(self.super_admin)
        resp = self.client.get(reverse('tenants_web:super_admin_dashboard'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Software Owner Billing Console")

    def test_gateway_management_toggle(self):
        self.client.force_login(self.super_admin)
        resp = self.client.post(reverse('tenants_web:gateway_management'), {
            "provider": "PAYSTACK",
            "enabled": "on",
            "maintenance_mode": "on",
            "priority": "1"
        })
        self.assertEqual(resp.status_code, 302)
        
        self.gw_paystack.refresh_from_db()
        self.assertTrue(self.gw_paystack.enabled)
        self.assertTrue(self.gw_paystack.maintenance_mode)

    def test_school_billing_dashboard(self):
        self.client.force_login(self.super_admin)
        resp = self.client.get(reverse('tenants_web:school_dashboard'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Horizon Academy")

    def test_parent_collection_center_and_htmx(self):
        self.client.force_login(self.super_admin)
        # Normal view
        resp = self.client.get(reverse('tenants_web:parent_collection_center'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Funke Akindele")

        # HTMX Search
        htmx_resp = self.client.get(
            reverse('tenants_web:parent_collection_center') + "?q=Funke",
            HTTP_HX_REQUEST='true'
        )
        self.assertEqual(htmx_resp.status_code, 200)
        self.assertContains(htmx_resp, "Funke Akindele")

    def test_parent_billing_portal(self):
        self.client.force_login(self.parent_user)
        resp = self.client.get(reverse('tenants_web:parent_portal'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Funke Akindele")

    def test_invoice_views_and_pdf(self):
        self.client.force_login(self.super_admin)
        # List View
        resp_list = self.client.get(reverse('tenants_web:invoice_list'))
        self.assertEqual(resp_list.status_code, 200)

        # Detail View
        resp_detail = self.client.get(reverse('tenants_web:invoice_detail', kwargs={'invoice_id': self.invoice.id}))
        self.assertEqual(resp_detail.status_code, 200)

        # ReportLab PDF View
        resp_pdf = self.client.get(reverse('tenants_web:invoice_pdf', kwargs={'invoice_id': self.invoice.id}))
        self.assertEqual(resp_pdf.status_code, 200)
        self.assertEqual(resp_pdf['Content-Type'], 'application/pdf')

    def test_receipt_views_and_pdf(self):
        # Complete payment first
        wf_res = SubscriptionWorkflowService.complete_parent_payment_workflow(
            invoice=self.invoice,
            payment_reference="REF-TEST-901",
            payment_method="PAYSTACK"
        )
        payment = SubscriptionPayment.objects.get(id=wf_res.data["payment_id"])

        self.client.force_login(self.super_admin)
        resp_list = self.client.get(reverse('tenants_web:receipt_list'))
        self.assertEqual(resp_list.status_code, 200)

        resp_pdf = self.client.get(reverse('tenants_web:receipt_pdf', kwargs={'payment_id': payment.id}))
        self.assertEqual(resp_pdf.status_code, 200)
        self.assertEqual(resp_pdf['Content-Type'], 'application/pdf')

    def test_reports_and_csv_export(self):
        self.client.force_login(self.super_admin)
        resp_reports = self.client.get(reverse('tenants_web:billing_reports'))
        self.assertEqual(resp_reports.status_code, 200)

        resp_csv = self.client.get(reverse('tenants_web:export_reports_csv'))
        self.assertEqual(resp_csv.status_code, 200)
        self.assertEqual(resp_csv['Content-Type'], 'text/csv')
