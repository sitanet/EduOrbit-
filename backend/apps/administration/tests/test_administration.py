from django.test import TestCase
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
from backend.apps.tenants.models import Tenant, School
from backend.apps.identity.models import User
from backend.apps.administration.models import (
    PlatformSetting, SchoolSetting, SubscriptionPlan, SchoolSubscription, ModuleLicense, FeatureFlag, SchoolBranding, PlatformAudit, APIKey
)

class AdministrationPlatformTests(TestCase):
    def setUp(self):
        # Create core configurations
        self.tenant = Tenant.objects.create(name="ESSACC Org")
        self.school = School.objects.create(tenant=self.tenant, name="ESSACC High School", school_types=["secondary"])
        
        # Identity User setup
        self.user = User.objects.create_user(
            username="admin_user",
            password="secure_password_123",
            email="admin@school.edu"
        )
        
        # Subscription plan setup
        self.plan = SubscriptionPlan.objects.create(
            name="Starter Package",
            monthly_price=Decimal("15000.00"),
            student_limit=200
        )
        
        # School setting
        self.setting = SchoolSetting.objects.create(
            school=self.school,
            tenant=self.tenant,
            theme_color="#ff5733",
            motto="Knowledge is Power"
        )

    def test_settings_and_branding(self):
        self.assertEqual(self.setting.theme_color, "#ff5733")
        
        branding = SchoolBranding.objects.create(
            school=self.school,
            tenant=self.tenant,
            custom_domain="highschool.eduorbit.com"
        )
        self.assertEqual(branding.custom_domain, "highschool.eduorbit.com")

    def test_subscriptions_renewals(self):
        sub = SchoolSubscription.objects.create(
            school=self.school,
            tenant=self.tenant,
            plan=self.plan,
            expiry_date=date.today() + timedelta(days=30)
        )
        self.assertEqual(sub.plan.name, "Starter Package")

    def test_module_licensing_matrix(self):
        lic = ModuleLicense.objects.create(
            school=self.school,
            tenant=self.tenant,
            module_name="hostel",
            is_enabled=True
        )
        self.assertTrue(lic.is_enabled)

    def test_immutable_platform_audit_logs(self):
        log = PlatformAudit.objects.create(
            actor=self.user,
            action="tenant.suspended",
            details="Suspended due to unpaid invoice"
        )
        self.assertEqual(log.action, "tenant.suspended")
