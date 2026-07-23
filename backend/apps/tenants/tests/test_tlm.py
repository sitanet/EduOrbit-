from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from backend.apps.tenants.models import Tenant, School, TenantSubscription, SubscriptionPlan
from backend.apps.tenants.services import TenantOnboardingService

class TenantLifecycleTests(TestCase):
    def test_tenant_and_school_onboarding(self):
        # Trigger onboarding
        tenant, school, admin_user = TenantOnboardingService.onboard_organization(
            org_name="Anchor Group",
            admin_email="admin@anchor.com",
            admin_username="anchor_admin",
            admin_password_plain="SecurePass123!",
            billing_model="parents_pay",
            school_name="Anchor Academy",
            school_types=["primary", "secondary"]
        )

        # 1. Verify Tenant (Organization)
        self.assertEqual(tenant.name, "Anchor Group")
        self.assertEqual(tenant.billing_model, "parents_pay")

        # 2. Verify School (Tenant scope)
        self.assertEqual(school.name, "Anchor Academy")
        self.assertEqual(school.tenant, tenant)
        self.assertIn("secondary", school.school_types)

        # 3. Verify Admin User association
        self.assertEqual(admin_user.username, "anchor_admin")
        self.assertTrue(admin_user.is_active)

        # 4. Verify Trial Subscription Provisioning
        subscription = TenantSubscription.objects.get(tenant=tenant)
        self.assertEqual(subscription.status, "trial")
        self.assertTrue(subscription.is_active_license())
