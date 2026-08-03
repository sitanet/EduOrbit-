"""
Phase 5 Mobile REST API & Backend Platform Test Suite for EduOrbit.
Verifies mobile configuration, JWT login & device push token registration,
single-request aggregated dashboards, mobile billing & payment APIs,
media PDF streaming, FCM push notifications, and offline delta sync.
"""

from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from backend.apps.identity.models import User
from backend.apps.tenants.models import (
    Tenant, School, SubscriptionInvoice, SubscriptionPayment,
    ParentSubscription, PaymentGatewaySetting, UserDevice, MobileNotification
)
from backend.apps.people.models import Person, ParentProfile, StudentProfile, FamilyRelationship
from backend.apps.tenants.services.subscription_workflow import SubscriptionWorkflowService


class Phase5MobileAPITestCase(TestCase):
    """
    Unit and Integration Test Suite for Phase 5 Mobile REST APIs.
    """
    def setUp(self):
        # 1. Setup Tenant & School
        self.tenant = Tenant.objects.create(
            name="Summit College",
            billing_model="PARENT_PAYS",
            parent_subscription_amount=Decimal("500.00"),
            compliance_threshold_percent=Decimal("80.00")
        )
        self.school = School.objects.create(
            tenant=self.tenant,
            name="Summit High School"
        )

        # 2. Setup Active Payment Gateway
        self.gw_paystack = PaymentGatewaySetting.objects.create(
            provider="PAYSTACK",
            display_name="Paystack Direct",
            enabled=True,
            priority=1
        )

        # 3. Setup Parent User & Profile
        self.parent_user = User.objects.create_user(
            username="parent_mobile@gmail.com",
            email="parent_mobile@gmail.com",
            password="mobilepassword123",
            tenant=self.tenant
        )

        self.parent_person = Person.objects.create(
            tenant=self.tenant,
            user=self.parent_user,
            person_number="PRN-501",
            first_name="Zainab",
            last_name="Balogun",
            gender="female",
            date_of_birth="1988-11-04"
        )
        self.parent_profile = ParentProfile.objects.create(
            tenant=self.tenant,
            person=self.parent_person,
            parent_number="PAR-2026-501"
        )

        self.student_person = Person.objects.create(
            tenant=self.tenant,
            person_number="STU-501",
            first_name="Farooq",
            last_name="Balogun",
            gender="male",
            date_of_birth="2017-02-20"
        )
        self.student_profile = StudentProfile.objects.create(
            tenant=self.tenant,
            person=self.student_person,
            student_number="STD-2026-501",
            current_school=self.school,
            enrollment_status="enrolled"
        )

        FamilyRelationship.objects.create(
            tenant=self.tenant,
            student=self.student_person,
            relative=self.parent_person,
            relationship_type="mother"
        )

        # Create Invoice
        wf_res = SubscriptionWorkflowService.create_parent_subscription_workflow(
            parent_profile=self.parent_profile,
            school=self.school,
            fee_per_child=Decimal("500.00")
        )
        self.invoice = SubscriptionInvoice.objects.get(id=wf_res.data["invoice_id"])

        self.client = Client()

    def test_mobile_config_api(self):
        url = reverse('tenants_api:mobile_config')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["success"])
        self.assertIn("feature_flags", resp.json()["data"])
        self.assertEqual(resp.json()["data"]["app_version"], "1.2.0")

    def test_jwt_login_and_device_registration(self):
        url = reverse('tenants_api:jwt_login')
        payload = {
            "username": "parent_mobile@gmail.com",
            "password": "mobilepassword123",
            "device_id": "fcm-dev-999",
            "push_token": "fcm_sample_token_xyz"
        }
        resp = self.client.post(url, data=payload, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["success"])
        self.assertIn("access", resp.json()["data"])

        # Verify UserDevice was registered
        device = UserDevice.objects.get(device_id="fcm-dev-999")
        self.assertEqual(device.user, self.parent_user)
        self.assertEqual(device.push_token, "fcm_sample_token_xyz")

    def test_single_request_role_dashboards(self):
        # Parent Dashboard
        url_parent = reverse('tenants_api:mobile_role_dashboard', kwargs={'role': 'parent'})
        resp_parent = self.client.get(url_parent)
        self.assertEqual(resp_parent.status_code, 200)
        self.assertTrue(resp_parent.json()["success"])
        self.assertEqual(resp_parent.json()["data"]["parent_name"], "Zainab Balogun")

        # School Admin Dashboard
        url_admin = reverse('tenants_api:mobile_role_dashboard', kwargs={'role': 'school-admin'})
        resp_admin = self.client.get(url_admin)
        self.assertEqual(resp_admin.status_code, 200)
        self.assertTrue(resp_admin.json()["success"])

    def test_mobile_billing_and_payment_apis(self):
        # Fee calculation
        calc_url = reverse('tenants_api:mobile_fee_calculation')
        calc_resp = self.client.get(calc_url)
        self.assertEqual(calc_resp.status_code, 200)
        self.assertEqual(calc_resp.json()["data"]["subtotal"], 500.0)

        # Payment Initialization
        init_url = reverse('tenants_api:mobile_payment_initialize')
        init_payload = {
            "invoice_id": str(self.invoice.id),
            "provider_name": "PAYSTACK"
        }
        init_resp = self.client.post(init_url, data=init_payload, content_type='application/json')
        self.assertEqual(init_resp.status_code, 200)
        self.assertTrue(init_resp.json()["success"])
        self.assertIn("payment_reference", init_resp.json()["data"])

    def test_media_pdf_streams(self):
        url = reverse('tenants_api:mobile_invoice_pdf', kwargs={'invoice_id': self.invoice.id})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/pdf')

    def test_notifications_and_delta_sync(self):
        # Create notification
        MobileNotification.objects.create(
            user=self.parent_user,
            title="Subscription Notice",
            body="Please renew your access."
        )

        notif_url = reverse('tenants_api:mobile_notifications')
        notif_resp = self.client.get(notif_url)
        self.assertEqual(notif_resp.status_code, 200)
        self.assertEqual(notif_resp.json()["data"]["unread_count"], 1)

        # Delta sync
        sync_url = reverse('tenants_api:mobile_delta_sync')
        sync_resp = self.client.get(sync_url)
        self.assertEqual(sync_resp.status_code, 200)
        self.assertIn("sync_token", sync_resp.json()["data"])
