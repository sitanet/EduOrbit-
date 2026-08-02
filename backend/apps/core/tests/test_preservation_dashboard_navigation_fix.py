"""
Dashboard Navigation Fix - Preservation Property Tests (Task 2)

These property-based tests capture baseline behavior patterns that MUST be preserved
during the dashboard navigation fix. They follow the observation-first methodology:

1. OBSERVE existing behavior on UNFIXED code FIRST
2. WRITE tests based on actual observed behavior, not assumptions
3. RUN tests on UNFIXED code - they MUST PASS to establish baseline
4. Use these tests as safety net during fix implementation

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10, 3.11, 3.12, 3.13**
"""

from django.test import TestCase, Client, RequestFactory
from django.contrib.auth import get_user_model
from django.urls import reverse
from backend.apps.tenants.models import Tenant, School, CustomDomain
from backend.apps.administration.models import SubscriptionPlan, SchoolSubscription
from backend.apps.portal.models import PortalAnnouncement, PortalNotification
from backend.apps.academic.models import AcademicYear, AcademicClass, Subject
from backend.apps.identity.models import Role, Permission
from backend.apps.ai.models import AIConversation, KnowledgeDocument
from backend.apps.core.middleware import TenantMiddleware
from hypothesis import given, strategies as st, settings, HealthCheck
from hypothesis.extra.django import TestCase as HypothesisTestCase
from datetime import datetime, timedelta
import random

User = get_user_model()


class DashboardPreservationTestCase(HypothesisTestCase):
    """Base test case for dashboard preservation property tests"""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data for preservation tests"""
        # Create test tenant with subdomain in branding_config (NOT as a field)
        cls.tenant = Tenant.objects.create(
            name="Test School Group",
            branding_config={"subdomain": "testgroup"}
        )
        
        # Create schools
        cls.school1 = School.objects.create(
            tenant=cls.tenant,
            name="Test Primary School",
            code="TPS"
        )
        cls.school2 = School.objects.create(
            tenant=cls.tenant,
            name="Test Secondary School", 
            code="TSS"
        )
        
        # Create subscription plan
        cls.plan = SubscriptionPlan.objects.create(
            name="Enterprise Plan",
            code="enterprise",
            price=9999.00
        )
        
        # Create users with different roles
        cls.superuser = User.objects.create_superuser(
            username='superuser',
            email='super@test.com',
            password='testpass123'
        )
        cls.superuser.is_staff = True
        cls.superuser.save()
        
        cls.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@test.com',
            password='testpass123'
        )
        cls.staff_user.is_staff = True
        cls.staff_user.save()
        
        cls.regular_user = User.objects.create_user(
            username='regularuser',
            email='user@test.com',
            password='testpass123'
        )
        
    def setUp(self):
        """Set up test client for each test"""
        self.client = Client()
        self.factory = RequestFactory()


class TestWorkingDashboardPreservation(DashboardPreservationTestCase):
    """
    Property 2: Preservation - Working Dashboard Functionality
    
    These tests capture the baseline behavior of the 5 working dashboard views
    that must NOT be affected by the bugfix. Tests MUST PASS on UNFIXED code.
    
    **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**
    """
    
    def test_control_center_dashboard_baseline_behavior(self):
        """
        Control Center (/administration/dashboard/) baseline behavior
        
        OBSERVED BEHAVIOR on UNFIXED code:
        - Requires authentication (redirects to /login/ if not authenticated)
        - Requires staff status (redirects non-staff to /portal/dashboard/)
        - Returns 200 OK with administration/dashboard.html template
        - Context includes: schools, plans, audits, active_school_id
        - Queries: School.objects.all(), SubscriptionPlan.objects.all(), PlatformAudit.objects.all()
        
        Requirement 3.1: Control Center functionality preserved
        """
        # Test unauthenticated access
        response = self.client.get('/administration/dashboard/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
        
        # Test non-staff access
        self.client.login(username='regularuser', password='testpass123')
        response = self.client.get('/administration/dashboard/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/portal/', response.url)
        
        # Test staff access (baseline behavior)
        self.client.login(username='superuser', password='testpass123')
        response = self.client.get('/administration/dashboard/')
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'administration/dashboard.html')
        
        # Verify expected context keys exist (baseline behavior)
        self.assertIn('schools', response.context)
        self.assertIn('plans', response.context)
        self.assertIn('audits', response.context)
        self.assertIn('active_school_id', response.context)
        
    def test_portal_dashboard_baseline_behavior(self):
        """
        Portal Dashboard (/portal/dashboard/) baseline behavior
        
        OBSERVED BEHAVIOR on UNFIXED code:
        - Requires authentication (redirects to /login/ if not authenticated)
        - Uses DashboardFactory.has_dashboard_access() for role checking
        - Returns 200 OK with portal/dashboard.html template
        - Context includes: schools, active_school, announcements, notifications
        - Tenant-aware queries for announcements/notifications
        
        Requirement 3.2: Portal Dashboard functionality preserved
        """
        # Test unauthenticated access
        response = self.client.get('/portal/dashboard/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
        
        # Test authenticated access (baseline behavior)
        self.client.login(username='regularuser', password='testpass123')
        
        # Create test data
        PortalAnnouncement.objects.create(
            tenant=self.tenant,
            title="Test Announcement",
            content="Test content"
        )
        
        response = self.client.get('/portal/dashboard/')
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'portal/dashboard.html')
        
        # Verify expected context keys exist (baseline behavior)
        self.assertIn('schools', response.context)
        self.assertIn('active_school', response.context)
        self.assertIn('announcements', response.context)
        
    def test_academic_dashboard_baseline_behavior(self):
        """
        Academic Dashboard (/academic/dashboard/) baseline behavior
        
        OBSERVED BEHAVIOR on UNFIXED code:
        - Requires authentication (redirects to /login/ if not authenticated)
        - Uses RoleRequiredMixin for role checking
        - Returns 200 OK with academic/dashboard.html template
        - Context includes: schools, active_school, years, classes, subjects
        - Uses getattr(request, 'tenant', None) pattern for safe tenant access
        
        Requirement 3.3: Academic Dashboard functionality preserved
        """
        # Test unauthenticated access
        response = self.client.get('/academic/dashboard/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
        
        # Test authenticated access (baseline behavior)
        self.client.login(username='superuser', password='testpass123')
        
        # Create test academic data
        year = AcademicYear.objects.create(
            tenant=self.tenant,
            school=self.school1,
            name="2024-2025",
            code="2024-2025",
            start_date=datetime.now().date(),
            end_date=(datetime.now() + timedelta(days=365)).date(),
            status='active'
        )
        
        response = self.client.get('/academic/dashboard/')
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'academic/dashboard.html')
        
        # Verify expected context keys exist (baseline behavior)
        self.assertIn('schools', response.context)
        self.assertIn('active_school', response.context)
        self.assertIn('years', response.context)
        self.assertIn('classes', response.context)
        self.assertIn('subjects', response.context)
        
    def test_roles_permissions_baseline_behavior(self):
        """
        Roles & Permissions (/identity/roles/) baseline behavior
        
        OBSERVED BEHAVIOR on UNFIXED code:
        - Requires authentication (redirects to /login/ if not authenticated)
        - Returns 200 OK with identity/role_matrix.html template
        - Context includes: roles, permissions
        - Queries all roles and permissions (not tenant-filtered)
        
        Requirement 3.4: Roles & Permissions functionality preserved
        """
        # Test unauthenticated access
        response = self.client.get('/identity/roles/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
        
        # Test authenticated access (baseline behavior)
        self.client.login(username='superuser', password='testpass123')
        
        # Create test role and permission data
        role = Role.objects.create(
            name="Test Role",
            code="test_role"
        )
        permission = Permission.objects.create(
            name="Test Permission",
            code="test_permission"
        )
        
        response = self.client.get('/identity/roles/')
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'identity/role_matrix.html')
        
        # Verify expected context keys exist (baseline behavior)
        self.assertIn('roles', response.context)
        self.assertIn('permissions', response.context)
        
    def test_ai_workspace_baseline_behavior(self):
        """
        AI Workspace (/ai/workspace/) baseline behavior
        
        OBSERVED BEHAVIOR on UNFIXED code:
        - Requires authentication (redirects to /login/ if not authenticated)
        - Returns 200 OK with ai/dashboard.html template
        - Context includes: schools, active_school, conversations, documents
        - Uses getattr(request, 'tenant', None) pattern for safe tenant access
        - Tenant-aware queries for conversations and documents
        
        Requirement 3.5: AI Workspace functionality preserved
        """
        # Test unauthenticated access
        response = self.client.get('/ai/workspace/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
        
        # Test authenticated access (baseline behavior)
        self.client.login(username='regularuser', password='testpass123')
        
        response = self.client.get('/ai/workspace/')
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ai/dashboard.html')
        
        # Verify expected context keys exist (baseline behavior)
        self.assertIn('schools', response.context)
        self.assertIn('active_school', response.context)
        self.assertIn('conversations', response.context)
        self.assertIn('documents', response.context)


class TestAuthenticationFlowPreservation(DashboardPreservationTestCase):
    """
    Property 3: Preservation - Authentication Flow Patterns
    
    Login, logout, and role-based redirects must remain unchanged.
    Tests MUST PASS on UNFIXED code.
    
    **Validates: Requirements 3.6, 3.7**
    """
    
    def test_login_redirects_based_on_user_role_baseline(self):
        """
        Login redirects to appropriate dashboard based on user role
        
        OBSERVED BEHAVIOR on UNFIXED code:
        - Uses DashboardFactory.get_dashboard_url(user) for role-based redirects
        - Superuser login redirects to /administration/dashboard/
        - Staff login redirects to appropriate tenant dashboard
        - Regular user login redirects to portal dashboard
        
        Requirement 3.6: Role-based dashboard redirection preserved
        """
        # Test superuser login redirect
        response = self.client.post('/login/', {
            'username': 'superuser',
            'password': 'testpass123'
        })
        
        # Should redirect or return HX-Redirect header
        self.assertTrue(
            response.status_code == 302 or 
            'HX-Redirect' in response.headers
        )
        
        # For superuser, should redirect to control center
        if response.status_code == 302:
            self.assertIn('/administration/dashboard/', response.url)
        elif 'HX-Redirect' in response.headers:
            self.assertIn('/administration/dashboard/', response.headers['HX-Redirect'])
    
    def test_logout_clears_session_baseline(self):
        """
        Logout clears session and redirects to login
        
        OBSERVED BEHAVIOR on UNFIXED code:
        - GET /login/?next=logout triggers logout
        - Clears Django session
        - Redirects to /login/
        - Subsequent access to protected resources requires re-authentication
        
        Requirement 3.7: Session management preserved
        """
        # Login first
        self.client.login(username='regularuser', password='testpass123')
        
        # Verify logged in
        response = self.client.get('/portal/dashboard/')
        self.assertEqual(response.status_code, 200)
        
        # Logout using the observed pattern
        response = self.client.get('/login/?next=logout')
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
        
        # Verify logged out - accessing protected page should redirect
        response = self.client.get('/portal/dashboard/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)


class TestTenantResolutionPreservation(DashboardPreservationTestCase):
    """
    Property 4: Preservation - Tenant Resolution Patterns
    
    TenantMiddleware behavior must remain unchanged.
    Tests MUST PASS on UNFIXED code.
    
    **Validates: Requirements 3.8, 3.9, 3.10, 3.11, 3.12**
    """
    
    def test_tenant_resolution_x_tenant_id_header_baseline(self):
        """
        X-Tenant-ID header resolution preserved
        
        OBSERVED BEHAVIOR on UNFIXED code:
        - TenantMiddleware checks request.headers.get('X-Tenant-ID')
        - Resolves tenant by UUID
        - Sets request.tenant to resolved tenant
        
        Requirement 3.8: Header-based tenant resolution preserved
        """
        request = self.factory.get('/academic/dashboard/', HTTP_X_TENANT_ID=str(self.tenant.id))
        request.user = self.superuser
        request.session = {}
        
        middleware = TenantMiddleware(lambda r: None)
        middleware(request)
        
        # Should resolve tenant from header
        self.assertIsNotNone(request.tenant)
        self.assertEqual(request.tenant.id, self.tenant.id)
        
    def test_tenant_resolution_custom_domain_baseline(self):
        """
        CustomDomain lookup resolution preserved
        
        OBSERVED BEHAVIOR on UNFIXED code:
        - TenantMiddleware checks for CustomDomain model
        - Looks up tenant by domain_name
        - Sets request.tenant to resolved tenant
        
        Requirement 3.9: Domain-based tenant resolution preserved
        """
        # Create custom domain
        custom_domain = CustomDomain.objects.create(
            tenant=self.tenant,
            domain_name="custom.test.com"
        )
        
        request = self.factory.get('/academic/dashboard/', HTTP_HOST='custom.test.com')
        request.user = self.superuser
        request.session = {}
        
        middleware = TenantMiddleware(lambda r: None)
        middleware(request)
        
        # Should resolve tenant from custom domain
        self.assertIsNotNone(request.tenant)
        self.assertEqual(request.tenant.id, self.tenant.id)
        
    def test_tenant_resolution_graceful_none_baseline(self):
        """
        Missing tenant sets request.tenant gracefully
        
        OBSERVED BEHAVIOR on UNFIXED code:
        - When no tenant can be resolved, middleware doesn't crash
        - Sets request.tenant to None or fallback tenant
        - Views handle None tenant gracefully using getattr pattern
        
        Requirement 3.10: Graceful handling of missing tenant preserved
        """
        request = self.factory.get('/academic/dashboard/', HTTP_HOST='nonexistent.test.com')
        request.user = self.superuser
        request.session = {}
        
        middleware = TenantMiddleware(lambda r: None)
        
        # Should not raise exception
        try:
            middleware(request)
        except Exception as e:
            self.fail(f"Middleware raised exception: {e}")
        
        # request.tenant should exist (may be None or fallback tenant)
        self.assertTrue(hasattr(request, 'tenant'))


class TestViewPatternsPreservation(DashboardPreservationTestCase):
    """
    Property 5: Preservation - View Query and Template Patterns
    
    Existing patterns for tenant access and template rendering preserved.
    Tests MUST PASS on UNFIXED code.
    
    **Validates: Requirements 3.11, 3.12, 3.13**
    """
    
    def test_getattr_tenant_pattern_baseline(self):
        """
        Views using getattr(request, 'tenant', None) pattern preserved
        
        OBSERVED BEHAVIOR on UNFIXED code:
        - Views use getattr(request, 'tenant', None) for safe tenant access
        - This pattern prevents AttributeError if tenant not set
        - Views handle None tenant gracefully
        
        Requirement 3.11: Safe tenant access pattern preserved
        """
        self.client.login(username='regularuser', password='testpass123')
        
        # Academic dashboard uses getattr pattern - should not crash
        response = self.client.get('/academic/dashboard/')
        
        # Should not crash even if tenant resolution fails
        self.assertEqual(response.status_code, 200)
        
    def test_template_rendering_baseline(self):
        """
        Template rendering patterns preserved
        
        OBSERVED BEHAVIOR on UNFIXED code:
        - Views use render(request, 'app/template.html', context)
        - Templates extend base/_document.html structure
        - Sidebar rendering works with base/_sidebar.html
        
        Requirement 3.12: Template structure preserved
        """
        self.client.login(username='superuser', password='testpass123')
        
        response = self.client.get('/administration/dashboard/')
        
        # Should render successfully with correct template
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'administration/dashboard.html')
        
    def test_authorization_patterns_baseline(self):
        """
        Authorization check patterns preserved
        
        OBSERVED BEHAVIOR on UNFIXED code:
        - Superuser-only views check is_staff or is_superuser
        - Non-authorized users get redirected to appropriate dashboard
        - Role-based access control via DashboardFactory or RoleRequiredMixin
        
        Requirement 3.13: Authorization preserved
        """
        self.client.login(username='regularuser', password='testpass123')
        
        # Control Center requires staff - should redirect non-staff
        response = self.client.get('/administration/dashboard/')
        
        self.assertIn(response.status_code, [302, 403])
        if response.status_code == 302:
            # Should redirect to appropriate dashboard
            self.assertIn('/portal/', response.url)


# Property-based test for comprehensive preservation checking
class TestDashboardPreservationProperties(DashboardPreservationTestCase):
    """
    Property-based tests for comprehensive preservation validation
    
    These tests use Hypothesis to generate many test cases and verify
    preservation properties hold across different scenarios.
    """
    
    @given(
        dashboard_url=st.sampled_from([
            '/administration/dashboard/',
            '/portal/dashboard/',
            '/academic/dashboard/',
            '/identity/roles/',
            '/ai/workspace/'
        ])
    )
    @settings(max_examples=10, deadline=5000, suppress_health_check=[HealthCheck.too_slow])
    def test_property_all_working_dashboards_require_authentication(self, dashboard_url):
        """
        Property: All working dashboards require authentication
        
        For ANY working dashboard URL, unauthenticated access should redirect to login.
        This property must hold before and after the fix.
        
        Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5
        """
        # Unauthenticated access should redirect to login
        response = self.client.get(dashboard_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
        
    @given(
        user_type=st.sampled_from(['superuser', 'staff', 'regular']),
        has_tenant=st.booleans()
    )
    @settings(max_examples=15, deadline=10000, suppress_health_check=[HealthCheck.too_slow])
    def test_property_tenant_resolution_always_sets_tenant_attribute(self, user_type, has_tenant):
        """
        Property: Tenant resolution always sets request.tenant attribute
        
        For ANY user type and tenant scenario, TenantMiddleware should set
        request.tenant attribute (may be None). This property must hold
        before and after the fix.
        
        Validates: Requirements 3.8, 3.9, 3.10, 3.11, 3.12
        """
        # Select user based on generated type
        if user_type == 'superuser':
            user = self.superuser
        elif user_type == 'staff':
            user = self.staff_user
        else:
            user = self.regular_user
            
        # Setup request with or without tenant context
        if has_tenant:
            request = self.factory.get('/academic/dashboard/', HTTP_X_TENANT_ID=str(self.tenant.id))
        else:
            request = self.factory.get('/academic/dashboard/', HTTP_HOST='localhost:8000')
        
        request.user = user
        request.session = {}
        
        middleware = TenantMiddleware(lambda r: None)
        middleware(request)
        
        # Property: request.tenant always exists after middleware
        self.assertTrue(hasattr(request, 'tenant'))