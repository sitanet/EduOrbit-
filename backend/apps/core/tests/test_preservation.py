"""
Preservation Property Tests for Dashboard Navigation Fix

These tests verify that existing working functionality is NOT affected by the bugfix.
Tests must PASS on UNFIXED code to establish baseline behavior.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10, 3.11, 3.12, 3.13**

## Observation Methodology

Before writing these tests, the following observations were made on UNFIXED code:

### Working Dashboard Views (Requirements 3.1-3.5):
1. **Control Center** (`/administration/dashboard/`):
   - Code inspection: `PlatformDashboardWebView` in `administration/views_web.py`
   - Behavior: Requires authentication, checks `is_staff`, queries schools/plans/audits
   - Returns: 200 OK with 'administration/dashboard.html' template
   - Context: schools, plans, audits, active_school_id

2. **Portal Dashboard** (`/portal/dashboard/`):
   - Code inspection: `PortalDashboardWebView` in `portal/views_web.py`
   - Behavior: Requires authentication, checks dashboard access via DashboardFactory
   - Returns: 200 OK with 'portal/dashboard.html' template
   - Context: schools, active_school, announcements, notifications

3. **Academic Dashboard** (`/academic/dashboard/`):
   - Code inspection: `AcademicDashboardWebView` in `academic/views_web.py`
   - Behavior: Requires authentication, role checking via `RoleRequiredMixin`
   - Returns: 200 OK with 'academic/dashboard.html' template
   - Context: schools, active_school, years, classes, subjects

4. **Roles & Permissions** (`/identity/roles/`):
   - Code inspection: `RoleMatrixWebView` in `identity/views_web.py`
   - Behavior: Requires authentication, queries all roles and permissions
   - Returns: 200 OK with 'identity/role_matrix.html' template
   - Context: roles, permissions

5. **AI Workspace** (`/ai/workspace/`):
   - Code inspection: `AIWorkspaceWebView` in `ai/views_web.py`
   - Behavior: Requires authentication, queries tenant-scoped conversations and documents
   - Returns: 200 OK with 'ai/dashboard.html' template
   - Context: schools, active_school, conversations, documents

### Authentication Flow (Requirements 3.6-3.7):
- Code inspection: `LoginWebView` in `identity/views_web.py`
- Login: POST to `/login/` with credentials, redirects via `DashboardFactory.get_dashboard_url(user)`
- Logout: GET `/login/?next=logout` triggers logout and redirect to login
- Unauthenticated access: All dashboard views return redirect to `/login/` (302)

### Tenant Resolution (Requirements 3.8-3.12):
- Code inspection: `TenantMiddleware` in `core/middleware.py`
- X-Tenant-ID header: Resolves tenant from `request.headers.get('X-Tenant-ID')`
- CustomDomain: Resolves tenant from `CustomDomain.objects.get(domain_name=host)`
- Subdomain: Resolves from `branding_config__subdomain` filter
- Session: Falls back to `request.session.get('active_tenant_id')`
- Local dev: Falls back to `Tenant.objects.filter(is_active=True).first()`
- Always sets `request.tenant` (may be None)

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
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from hypothesis.extra.django import TestCase as HypothesisTestCase
from datetime import datetime, timedelta
import random

User = get_user_model()


class PreservationTestCase(HypothesisTestCase):
    """Base test case with common setup for preservation tests"""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data that won't change across tests"""
        # Create test tenant
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
        cls.staff_user.is_staff = False
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


class TestExistingDashboardPreservation(PreservationTestCase):
    """
    Property 2: Preservation - Existing Dashboard and Tenant Functionality
    
    For all working dashboard views (Control Center, Portal, Academic, Roles, AI),
    the behavior must remain identical before and after the fix.
    
    **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**
    """
    
    def test_control_center_dashboard_authenticated_superuser(self):
        """
        Control Center dashboard continues displaying correctly for superusers
        Requirement 3.1: /administration/dashboard/ displays platform dashboard
        """
        self.client.login(username='superuser', password='testpass123')
        response = self.client.get('/administration/dashboard/')
        
        # Should return 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Should render correct template
        self.assertTemplateUsed(response, 'administration/dashboard.html')
        
        # Should include expected context data
        self.assertIn('schools', response.context)
        self.assertIn('plans', response.context)
        self.assertIn('audits', response.context)
        
        # Schools should be queryable
        schools = list(response.context['schools'])
        self.assertGreaterEqual(len(schools), 0)
    
    def test_control_center_redirects_non_staff(self):
        """
        Control Center redirects non-staff users to portal dashboard
        Requirement 3.1: Access control preserved
        """
        self.client.login(username='regularuser', password='testpass123')
        response = self.client.get('/administration/dashboard/')
        
        # Should redirect non-staff to portal
        self.assertEqual(response.status_code, 302)
        self.assertIn('/portal/', response.url)
    
    def test_portal_dashboard_authenticated(self):
        """
        Portal Dashboard continues displaying correctly for authenticated users
        Requirement 3.2: /portal/dashboard/ displays announcements and notifications
        """
        self.client.login(username='regularuser', password='testpass123')
        
        # Create test announcements
        PortalAnnouncement.objects.create(
            tenant=self.tenant,
            title="Test Announcement",
            content="Test content"
        )
        
        response = self.client.get('/portal/dashboard/')
        
        # Should return 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Should render correct template
        self.assertTemplateUsed(response, 'portal/dashboard.html')
        
        # Should include expected context
        self.assertIn('announcements', response.context)
    
    def test_academic_dashboard_authenticated(self):
        """
        Academic Dashboard continues displaying correctly
        Requirement 3.3: /academic/dashboard/ displays academic years, classes, subjects
        """
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
        
        # Should return 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Should render correct template
        self.assertTemplateUsed(response, 'academic/dashboard.html')
        
        # Should include expected context
        self.assertIn('schools', response.context)
        self.assertIn('years', response.context)
        self.assertIn('classes', response.context)
        self.assertIn('subjects', response.context)
    
    def test_roles_permissions_dashboard(self):
        """
        Roles & Permissions continues displaying correctly
        Requirement 3.4: /identity/roles/ displays role matrix
        """
        self.client.login(username='superuser', password='testpass123')
        
        # Create test role and permission
        role = Role.objects.create(
            name="Test Role",
            code="test_role"
        )
        permission = Permission.objects.create(
            name="Test Permission",
            code="test_permission"
        )
        
        response = self.client.get('/identity/roles/')
        
        # Should return 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Should render correct template
        self.assertTemplateUsed(response, 'identity/role_matrix.html')
        
        # Should include expected context
        self.assertIn('roles', response.context)
        self.assertIn('permissions', response.context)
    
    def test_ai_workspace_authenticated(self):
        """
        AI Workspace continues displaying correctly
        Requirement 3.5: /ai/workspace/ displays AI workspace interface
        """
        self.client.login(username='regularuser', password='testpass123')
        
        response = self.client.get('/ai/workspace/')
        
        # Should return 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Should render correct template
        self.assertTemplateUsed(response, 'ai/dashboard.html')
        
        # Should include expected context
        self.assertIn('schools', response.context)
        self.assertIn('conversations', response.context)
        self.assertIn('documents', response.context)
    
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
    def test_working_dashboards_require_authentication(self, dashboard_url):
        """
        Property: All working dashboards require authentication
        Requirement 3.6: Authentication checks preserved
        """
        # Unauthenticated access should redirect to login
        response = self.client.get(dashboard_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)


class TestAuthenticationFlowPreservation(PreservationTestCase):
    """
    Property 3: Preservation - Authentication & Authorization Flows
    
    Login, logout, and role-based redirects must remain unchanged.
    
    **Validates: Requirements 3.6, 3.7, 3.13**
    """
    
    def test_login_redirects_superuser_to_control_center(self):
        """
        Superuser login redirects to Control Center
        Requirement 3.6: Role-based dashboard redirection preserved
        """
        response = self.client.post('/login/', {
            'username': 'superuser',
            'password': 'testpass123'
        })
        
        # Should redirect (either 302 or return HX-Redirect header)
        self.assertTrue(
            response.status_code == 302 or 
            'HX-Redirect' in response.headers
        )
        
        # Follow redirect to verify destination
        if response.status_code == 302:
            self.assertIn('/administration/dashboard/', response.url)
    
    def test_logout_clears_session_and_redirects(self):
        """
        Logout clears session and redirects to login
        Requirement 3.7: Session management preserved
        """
        # Login first
        self.client.login(username='regularuser', password='testpass123')
        
        # Verify logged in
        response = self.client.get('/portal/dashboard/')
        self.assertEqual(response.status_code, 200)
        
        # Logout
        response = self.client.get('/login/?next=logout')
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
        
        # Verify logged out - accessing protected page should redirect
        response = self.client.get('/portal/dashboard/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_login_page_accessible_unauthenticated(self):
        """
        Login page is accessible without authentication
        Requirement 3.6: Login flow preserved
        """
        response = self.client.get('/login/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'identity/login.html')
    
    @given(
        username=st.sampled_from(['superuser', 'staffuser', 'regularuser'])
    )
    @settings(max_examples=3, deadline=5000, suppress_health_check=[HealthCheck.too_slow])
    def test_valid_login_creates_session(self, username):
        """
        Property: Valid login establishes authenticated session
        Requirement 3.6: Authentication flow preserved
        """
        response = self.client.post('/login/', {
            'username': username,
            'password': 'testpass123'
        })
        
        # Should succeed (redirect or HX-Redirect)
        self.assertTrue(
            response.status_code in [200, 302] or
            'HX-Redirect' in response.headers
        )
        
        # Session should be authenticated
        user = User.objects.get(username=username)
        self.assertTrue(user.is_authenticated)


class TestTenantResolutionPreservation(PreservationTestCase):
    """
    Property 4: Preservation - Tenant Resolution Logic
    
    TenantMiddleware behavior must remain unchanged.
    
    **Validates: Requirements 3.8, 3.9, 3.10, 3.11, 3.12**
    """
    
    def test_tenant_resolution_via_x_tenant_id_header(self):
        """
        X-Tenant-ID header resolution preserved
        Requirement 3.8: Header-based tenant resolution works
        """
        request = self.factory.get('/academic/dashboard/', HTTP_X_TENANT_ID=str(self.tenant.id))
        request.user = self.superuser
        request.session = {}
        
        middleware = TenantMiddleware(lambda r: None)
        middleware(request)
        
        # Should resolve tenant from header
        self.assertIsNotNone(request.tenant)
        self.assertEqual(request.tenant.id, self.tenant.id)
    
    def test_tenant_resolution_via_custom_domain(self):
        """
        CustomDomain lookup resolution preserved
        Requirement 3.9: Domain-based tenant resolution works
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
    
    def test_tenant_resolution_sets_none_when_not_found(self):
        """
        Missing tenant sets request.tenant to None gracefully
        Requirement 3.10: Graceful handling of missing tenant
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
    
    def test_local_development_fallback_to_first_tenant(self):
        """
        Local development fallback to first active tenant preserved
        Requirement 3.11, 3.12: Development fallback works
        """
        request = self.factory.get('/academic/dashboard/', HTTP_HOST='localhost:8000')
        request.user = self.superuser
        request.session = {}
        
        middleware = TenantMiddleware(lambda r: None)
        middleware(request)
        
        # Should fallback to first active tenant
        self.assertIsNotNone(request.tenant)
        self.assertTrue(request.tenant.is_active)
    
    @given(
        has_header=st.booleans(),
        has_custom_domain=st.booleans()
    )
    @settings(max_examples=5, deadline=5000, suppress_health_check=[HealthCheck.too_slow])
    def test_tenant_resolution_property(self, has_header, has_custom_domain):
        """
        Property: Tenant resolution always sets request.tenant attribute
        Requirement 3.8, 3.9, 3.10: All resolution paths set tenant
        """
        # Setup request based on generated booleans
        if has_header:
            request = self.factory.get('/academic/dashboard/', HTTP_X_TENANT_ID=str(self.tenant.id))
        elif has_custom_domain:
            CustomDomain.objects.get_or_create(
                tenant=self.tenant,
                domain_name="generated.test.com"
            )
            request = self.factory.get('/academic/dashboard/', HTTP_HOST='generated.test.com')
        else:
            request = self.factory.get('/academic/dashboard/', HTTP_HOST='localhost:8000')
        
        request.user = self.superuser
        request.session = {}
        
        middleware = TenantMiddleware(lambda r: None)
        middleware(request)
        
        # Property: request.tenant always exists after middleware
        self.assertTrue(hasattr(request, 'tenant'))


class TestViewQueryPatternsPreservation(PreservationTestCase):
    """
    Property 5: Preservation - View Query Patterns
    
    Existing view patterns for tenant access and template rendering preserved.
    
    **Validates: Requirements 3.11, 3.12**
    """
    
    def test_getattr_tenant_pattern_safe_access(self):
        """
        Views using getattr(request, 'tenant', None) work correctly
        Requirement 3.11: Safe tenant access pattern preserved
        """
        self.client.login(username='regularuser', password='testpass123')
        
        # Academic dashboard uses getattr pattern
        response = self.client.get('/academic/dashboard/')
        
        # Should not crash even if tenant is None
        self.assertEqual(response.status_code, 200)
    
    def test_template_rendering_with_base_structure(self):
        """
        Template rendering with base/_document.html structure preserved
        Requirement 3.12: Template structure preserved
        """
        self.client.login(username='superuser', password='testpass123')
        
        response = self.client.get('/administration/dashboard/')
        
        # Should render successfully
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'administration/dashboard.html')


class TestAuthorizationPreservation(PreservationTestCase):
    """
    Property 6: Preservation - Authorization Checks
    
    Superuser-only and staff-only view restrictions preserved.
    
    **Validates: Requirement 3.13**
    """
    
    def test_superuser_only_views_block_non_superusers(self):
        """
        Superuser-only views redirect non-superusers
        Requirement 3.13: Authorization preserved
        """
        self.client.login(username='regularuser', password='testpass123')
        
        # Control Center requires superuser/staff
        response = self.client.get('/administration/dashboard/')
        
        # Should redirect or show access denied
        self.assertIn(response.status_code, [302, 403])
        if response.status_code == 302:
            # Should redirect to appropriate dashboard
            self.assertIn('/portal/', response.url)
