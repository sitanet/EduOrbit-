from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from backend.apps.tenants.models import Tenant, SubscriptionPlan, TenantSubscription
from backend.apps.tenants.services.subscription import SubscriptionService, SubscriptionValidationService
from backend.apps.tenants.services.gateways import OPayGateway, PaystackGateway

class PlatformBillingTestCase(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Apex Education Network", billing_model="SCHOOL_PAY")
        self.plan = SubscriptionPlan.objects.create(
            name="Enterprise Tier",
            description="All inclusive plan",
            billing_model="SCHOOL_PAY",
            monthly_price=50000.00,
            termly_price=135000.00,
            yearly_price=380000.00,
            trial_days=14,
            grace_period_days=7,
            max_students=1000,
            max_staff=100,
            parent_portal_enabled=True,
            mobile_app_enabled=True,
            lms_enabled=True,
            cbt_enabled=True
        )
        self.client = APIClient()

    def test_subscription_creation_and_validation(self):
        # 1. Activate School Pay Subscription
        sub_res = SubscriptionService.create_tenant_subscription(
            tenant=self.tenant,
            plan=self.plan,
            billing_cycle="MONTHLY",
            billing_model="SCHOOL_PAY"
        )
        self.assertEqual(sub_res["status"], "success")

        # 2. Access Validation
        val = SubscriptionValidationService.validate_tenant_access(tenant=self.tenant, module_name="lms")
        self.assertTrue(val["is_valid"])
        self.assertEqual(val["status"], "ACTIVE")

        # 3. Limit Check
        limits = SubscriptionValidationService.validate_limits(tenant=self.tenant, current_students=500, current_staff=50)
        self.assertTrue(limits["within_limits"])

        # 4. Limit Exceeded Check
        over_limits = SubscriptionValidationService.validate_limits(tenant=self.tenant, current_students=1500, current_staff=50)
        self.assertFalse(over_limits["within_limits"])

    def test_opay_and_paystack_gateways_and_renewal(self):
        # 1. Charge via OPay
        opay = OPayGateway()
        opay_res = opay.charge(amount=50000.00, reference="OPAY-REF-001", customer_email="finance@apex.edu")
        self.assertEqual(opay_res["status"], "success")
        self.assertEqual(opay_res["provider"], "OPay")

        # 2. Charge via Paystack
        paystack = PaystackGateway()
        pstk_res = paystack.charge(amount=50000.00, reference="PSTK-REF-001", customer_email="finance@apex.edu")
        self.assertEqual(pstk_res["status"], "success")
        self.assertEqual(pstk_res["provider"], "Paystack")

        # 3. Renew Subscription via Paystack Provider
        sub_res = SubscriptionService.create_tenant_subscription(tenant=self.tenant, plan=self.plan)
        sub = TenantSubscription.objects.get(id=sub_res["subscription_id"])
        sub.payment_provider = "Paystack"
        sub.save()
        
        renew_res = SubscriptionService.renew_subscription(subscription=sub, payment_reference="PSTK-REF-001")
        self.assertEqual(renew_res["status"], "success")

    def test_platform_subscription_api_endpoints(self):
        # 1. List Plans API
        plans_url = '/tenants/api/v1/subscription/plans/'
        resp = self.client.get(plans_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data["count"] > 0)

        # 2. Subscribe API
        sub_url = '/tenants/api/v1/subscription/subscribe/'
        payload = {
            "tenant_id": str(self.tenant.id),
            "plan_id": str(self.plan.id),
            "billing_cycle": "TERMLY",
            "billing_model": "SCHOOL_PAY"
        }
        sub_resp = self.client.post(sub_url, payload, format='json')
        self.assertEqual(sub_resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(sub_resp.data["status"], "success")

        # 3. Status API
        status_url = f'/tenants/api/v1/subscription/status/?tenant_id={self.tenant.id}'
        stat_resp = self.client.get(status_url)
        self.assertEqual(stat_resp.status_code, status.HTTP_200_OK)
        self.assertTrue(stat_resp.data["data"]["is_valid"])

        # 4. OPay Webhook API
        opay_wh_url = '/tenants/api/v1/subscription/webhook/opay/'
        opay_wh_payload = {"reference": "OPAY-REF-001", "event": "payment.successful"}
        opay_wh_resp = self.client.post(opay_wh_url, opay_wh_payload, format='json')
        self.assertEqual(opay_wh_resp.status_code, status.HTTP_200_OK)
        self.assertTrue(opay_wh_resp.data["data"]["processed"])

        # 5. Paystack Webhook API
        pstk_wh_url = '/tenants/api/v1/subscription/webhook/paystack/'
        pstk_wh_payload = {"reference": "PSTK-REF-001", "event": "charge.success"}
        pstk_wh_resp = self.client.post(pstk_wh_url, pstk_wh_payload, format='json')
        self.assertEqual(pstk_wh_resp.status_code, status.HTTP_200_OK)
        self.assertTrue(pstk_wh_resp.data["data"]["processed"])
