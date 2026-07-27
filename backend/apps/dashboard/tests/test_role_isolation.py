"""
EduOrbit ERP v3.0.1 — Role Isolation Test Suite
================================================
Tests every dashboard view for:
  1. Correct HTTP 200 for the right role
  2. HTTP 302/403 for wrong roles
  3. Login router sends to correct URL
  4. DashboardFactory resolves correctly
"""
import os
import sys
import django

sys.path.insert(0, r'c:\Users\user\Desktop\Development\SMS')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings.local')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from backend.apps.dashboard.services import (
    DashboardFactory,
    ROLE_SUPER_ADMIN, ROLE_SCHOOL_ADMIN, ROLE_TEACHER, ROLE_STUDENT,
    ROLE_PARENT, ROLE_FINANCE, ROLE_HR, ROLE_LIBRARIAN, ROLE_WARDEN,
    ROLE_TRANSPORT, ROLE_NURSE, ROLE_EXAM_OFFICER,
)

User = get_user_model()


class DashboardFactoryTests(TestCase):
    """Unit tests for DashboardFactory role resolution."""

    def setUp(self):
        self.groups = {}
        for name in ['school_admin', 'teacher', 'student', 'parent',
                     'finance_officer', 'hr_admin', 'librarian', 'warden',
                     'transport_officer', 'nurse', 'exam_officer']:
            g, _ = Group.objects.get_or_create(name=name)
            self.groups[name] = g

    def _make_user(self, username, group_name=None, is_superuser=False):
        user = User.objects.create_user(
            username=username,
            email=f'{username}@test.eduorbit.com',
            password='Test@1234',
            is_superuser=is_superuser,
            is_staff=is_superuser
        )
        if group_name:
            user.groups.add(self.groups[group_name])
        return user

    def test_superuser_resolves_to_super_admin(self):
        user = self._make_user('testsuper', is_superuser=True)
        self.assertEqual(DashboardFactory.resolve_role(user), ROLE_SUPER_ADMIN)

    def test_school_admin_group_resolves_correctly(self):
        user = self._make_user('testadmin', 'school_admin')
        self.assertEqual(DashboardFactory.resolve_role(user), ROLE_SCHOOL_ADMIN)

    def test_teacher_group_resolves_correctly(self):
        user = self._make_user('testteacher', 'teacher')
        self.assertEqual(DashboardFactory.resolve_role(user), ROLE_TEACHER)

    def test_student_group_resolves_correctly(self):
        user = self._make_user('teststudent', 'student')
        self.assertEqual(DashboardFactory.resolve_role(user), ROLE_STUDENT)

    def test_parent_group_resolves_correctly(self):
        user = self._make_user('testparent', 'parent')
        self.assertEqual(DashboardFactory.resolve_role(user), ROLE_PARENT)

    def test_finance_group_resolves_correctly(self):
        user = self._make_user('testfinance', 'finance_officer')
        self.assertEqual(DashboardFactory.resolve_role(user), ROLE_FINANCE)

    def test_hr_group_resolves_correctly(self):
        user = self._make_user('testhr', 'hr_admin')
        self.assertEqual(DashboardFactory.resolve_role(user), ROLE_HR)

    def test_librarian_group_resolves_correctly(self):
        user = self._make_user('testlib', 'librarian')
        self.assertEqual(DashboardFactory.resolve_role(user), ROLE_LIBRARIAN)

    def test_warden_group_resolves_correctly(self):
        user = self._make_user('testwarden', 'warden')
        self.assertEqual(DashboardFactory.resolve_role(user), ROLE_WARDEN)

    def test_transport_group_resolves_correctly(self):
        user = self._make_user('testtransport', 'transport_officer')
        self.assertEqual(DashboardFactory.resolve_role(user), ROLE_TRANSPORT)

    def test_nurse_group_resolves_correctly(self):
        user = self._make_user('testnurse', 'nurse')
        self.assertEqual(DashboardFactory.resolve_role(user), ROLE_NURSE)

    def test_exam_group_resolves_correctly(self):
        user = self._make_user('testexam', 'exam_officer')
        self.assertEqual(DashboardFactory.resolve_role(user), ROLE_EXAM_OFFICER)

    def test_get_dashboard_url_for_teacher(self):
        user = self._make_user('urltest', 'teacher')
        url = DashboardFactory.get_dashboard_url(user)
        self.assertEqual(url, '/dashboard/teacher/')

    def test_has_dashboard_access_same_role(self):
        user = self._make_user('accesstest', 'nurse')
        self.assertTrue(DashboardFactory.has_dashboard_access(user, ROLE_NURSE))

    def test_has_dashboard_access_wrong_role_denied(self):
        user = self._make_user('denytest', 'nurse')
        self.assertFalse(DashboardFactory.has_dashboard_access(user, ROLE_FINANCE))

    def test_superuser_can_access_any_dashboard(self):
        user = self._make_user('superaccess', is_superuser=True)
        for role in [ROLE_TEACHER, ROLE_STUDENT, ROLE_NURSE, ROLE_FINANCE]:
            self.assertTrue(DashboardFactory.has_dashboard_access(user, role))


class DashboardViewIsolationTests(TestCase):
    """
    HTTP-level test: verify each role gets 200 on their own dashboard
    and 302/403 when they try to access another role's dashboard.
    """

    def setUp(self):
        self.client = Client()
        self.groups = {}
        for name in ['school_admin', 'teacher', 'student', 'parent',
                     'finance_officer', 'hr_admin', 'librarian', 'warden',
                     'transport_officer', 'nurse', 'exam_officer']:
            g, _ = Group.objects.get_or_create(name=name)
            self.groups[name] = g

    def _make_user(self, username, group_name=None, is_superuser=False):
        user = User.objects.create_user(
            username=username,
            email=f'{username}@test.eduorbit.com',
            password='Test@1234',
            is_superuser=is_superuser,
            is_staff=is_superuser
        )
        if group_name:
            user.groups.add(self.groups[group_name])
        return user

    def _login(self, username):
        self.client.force_login(User.objects.get(username=username))

    def test_teacher_accesses_own_dashboard_200(self):
        self._make_user('http_teacher', 'teacher')
        self._login('http_teacher')
        r = self.client.get('/dashboard/teacher/')
        self.assertEqual(r.status_code, 200)

    def test_teacher_cannot_access_school_admin_dashboard(self):
        self._make_user('http_teacher2', 'teacher')
        self._login('http_teacher2')
        r = self.client.get('/dashboard/school-admin/')
        self.assertIn(r.status_code, [302, 403])

    def test_student_accesses_own_dashboard_200(self):
        self._make_user('http_student', 'student')
        self._login('http_student')
        r = self.client.get('/dashboard/student/')
        self.assertEqual(r.status_code, 200)

    def test_student_cannot_access_finance_dashboard(self):
        self._make_user('http_student2', 'student')
        self._login('http_student2')
        r = self.client.get('/dashboard/finance/')
        self.assertIn(r.status_code, [302, 403])

    def test_nurse_accesses_clinic_dashboard_200(self):
        self._make_user('http_nurse', 'nurse')
        self._login('http_nurse')
        r = self.client.get('/dashboard/clinic/')
        self.assertEqual(r.status_code, 200)

    def test_nurse_cannot_access_hr_dashboard(self):
        self._make_user('http_nurse2', 'nurse')
        self._login('http_nurse2')
        r = self.client.get('/dashboard/hr/')
        self.assertIn(r.status_code, [302, 403])

    def test_superuser_can_access_super_admin_dashboard(self):
        self._make_user('http_super', is_superuser=True)
        self._login('http_super')
        r = self.client.get('/dashboard/super-admin/')
        self.assertEqual(r.status_code, 200)

    def test_superuser_can_also_access_school_admin_dashboard(self):
        self._make_user('http_super2', is_superuser=True)
        self._login('http_super2')
        r = self.client.get('/dashboard/school-admin/')
        self.assertEqual(r.status_code, 200)

    def test_unauthenticated_gets_redirect_to_login(self):
        r = self.client.get('/dashboard/teacher/')
        self.assertEqual(r.status_code, 302)
        self.assertIn('/login/', r['Location'])

    def test_login_router_uses_factory_not_username(self):
        """Ensure DashboardFactory.get_dashboard_url() is used, not username string matching."""
        user = self._make_user('finance_user_xyz', 'finance_officer')
        url = DashboardFactory.get_dashboard_url(user)
        self.assertEqual(url, '/dashboard/finance/')
        # The username 'finance_user_xyz' should NOT match any old string checks
        # but DashboardFactory resolves from group membership correctly.
