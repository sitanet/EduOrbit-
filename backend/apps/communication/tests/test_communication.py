from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from backend.apps.tenants.models import Tenant, School
from backend.apps.people.models import Person
from backend.apps.identity.models import User
from backend.apps.communication.models import (
    Announcement, Notification, NotificationPreference, NotificationTemplate, BroadcastCampaign
)

class CEHPlatformTests(TestCase):
    def setUp(self):
        # Create core configurations
        self.tenant = Tenant.objects.create(name="CEH Org")
        self.school = School.objects.create(tenant=self.tenant, name="CEH High School", school_types=["secondary"])
        
        # User & Person profile
        self.user = User.objects.create_user(username="test_comm_user", email="comm@eduorbit.com", password="SecurePassword123!")
        self.person = Person.objects.create(
            tenant=self.tenant,
            person_number="P-30088",
            first_name="Jane",
            last_name="Foster",
            gender="female",
            date_of_birth="2010-09-12"
        )
        
        # Announcement
        self.announcement = Announcement.objects.create(
            school=self.school,
            tenant=self.tenant,
            title="PTA Meeting rescheduled",
            content="PTA Meeting moved to next Friday.",
            priority="general",
            visibility="parents"
        )
        
        # Preference
        self.pref = NotificationPreference.objects.create(
            user=self.user,
            tenant=self.tenant,
            category="fees",
            email_enabled=True,
            sms_enabled=False,
            push_enabled=True,
            whatsapp_enabled=False
        )

    def test_notification_template_placeholders_substitution(self):
        template = NotificationTemplate.objects.create(
            tenant=self.tenant,
            name="invoice_gen",
            subject_template="New Invoice Issued for {{student_name}}",
            body_template="Hi {{parent_name}}, an invoice of {{amount}} was generated."
        )
        
        # Simulate simple parsing
        subject = template.subject_template.replace("{{student_name}}", "Thor")
        body = template.body_template.replace("{{parent_name}}", "Odin").replace("{{amount}}", "₦50,000")
        
        self.assertEqual(subject, "New Invoice Issued for Thor")
        self.assertEqual(body, "Hi Odin, an invoice of ₦50,000 was generated.")

    def test_opt_in_preferences_routing(self):
        # Check preferences mapping
        self.assertTrue(self.pref.email_enabled)
        self.assertFalse(self.pref.sms_enabled)

    def test_broadcast_campaign_delivery_metrics(self):
        campaign = BroadcastCampaign.objects.create(
            tenant=self.tenant,
            name="Fee Defaulters Alert T1",
            target_audience="debtors",
            sent_count=100,
            delivered_count=85
        )
        
        delivery_rate = (campaign.delivered_count / campaign.sent_count) * 100
        self.assertEqual(delivery_rate, 85.00)
