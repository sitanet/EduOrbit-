from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from backend.apps.identity.models import User, UserSession, PasswordHistory, Role, Permission, TenantMembership
from backend.apps.identity.services import IdentityService, AuthorizationService
from backend.apps.tenants.models import Tenant

class IdentityAndAccessTests(TestCase):
    def setUp(self):
        # Setup test tenant
        self.tenant = Tenant.objects.create(name="Secondary School")
        
        # Setup test user profile
        self.user = User.objects.create_user(
            username="admin_user",
            email="admin@secschool.com",
            password="SecurePassword123"
        )
        
    def test_custom_user_creation(self):
        self.assertEqual(self.user.username, "admin_user")
        self.assertTrue(self.user.is_active)
        self.assertFalse(self.user.mfa_enabled)

    def test_password_history_validation(self):
        # Set initial history entry
        PasswordHistory.objects.create(user=self.user, password_hash=self.user.password)
        
        # Changing password to same one should raise ValueError
        with self.assertRaises(ValueError):
            IdentityService.record_password_change(self.user, "SecurePassword123")

    def test_dynamic_permission_evaluation(self):
        # Create permissions
        view_users = Permission.objects.create(
            code="users.view",
            name="View Users",
            module="Users"
        )
        
        # Create Role
        admin_role = Role.objects.create(name="School Admin", code="school_admin", tenant=self.tenant)
        admin_role.permissions.add(view_users)
        
        # Assign role
        IdentityService.record_password_change(self.user, "NewStrongPassword456")
        membership = AuthorizationService.assign_user_role(self.user, admin_role, self.tenant.id)
        
        self.assertEqual(membership.status, "active")
        
        # Evaluate permissions
        has_perm = AuthorizationService.check_user_permission(self.user, "users.view", self.tenant.id)
        self.assertTrue(has_perm)
        
        # Check non-existent permissions
        has_missing = AuthorizationService.check_user_permission(self.user, "users.delete", self.tenant.id)
        self.assertFalse(has_missing)
