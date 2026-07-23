from django.test import TestCase
from django.utils import timezone
from backend.apps.tenants.models import Tenant, School
from backend.apps.identity.models import User
from backend.apps.portal.models import (
    PortalProfile, PortalShortcut, PortalAnnouncement, PortalBookmark, PortalActivity, PortalSession, PortalNotification, PortalPreference
)

class PortalPlatformTests(TestCase):
    def setUp(self):
        # Create core configurations
        self.tenant = Tenant.objects.create(name="EPSSP Org")
        self.school = School.objects.create(tenant=self.tenant, name="EPSSP High School", school_types=["secondary"])
        
        # Identity User setup
        self.user = User.objects.create_user(
            username="portal_user",
            password="secure_password_123",
            email="portal@school.edu"
        )
        
        # Profile preferences
        self.profile = PortalProfile.objects.create(
            user=self.user,
            tenant=self.tenant,
            theme="dark",
            timezone="Africa/Lagos"
        )
        self.shortcut = PortalShortcut.objects.create(
            profile=self.profile,
            tenant=self.tenant,
            name="Check Grades Summary",
            target_url="/portal/results/"
        )

    def test_portal_shortcuts_preferences(self):
        self.assertEqual(self.profile.theme, "dark")
        self.assertEqual(self.shortcut.name, "Check Grades Summary")

    def test_portal_announcements_routing(self):
        ann = PortalAnnouncement.objects.create(
            school=self.school,
            tenant=self.tenant,
            title="End of Term Assembly",
            body="All parents must join at 10am in auditorium.",
            target_role="parent"
        )
        self.assertEqual(ann.target_role, "parent")

    def test_portal_notifications_inbox(self):
        notif = PortalNotification.objects.create(
            user=self.user,
            tenant=self.tenant,
            title="Library Loan Overdue Alert",
            body="Please return the Chemistry Textbook today.",
            is_read=False
        )
        self.assertFalse(notif.is_read)
        
        notif.is_read = True
        notif.save()
        self.assertTrue(notif.is_read)
