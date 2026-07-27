"""
EduOrbit ERP v3.0.1 — Role-Isolated Dashboard Views
=====================================================
Each dashboard view:
  1. Requires authentication (Layer 1 — URL access)
  2. Validates the user's role against the required dashboard role (Layer 2 — view access)
  3. Returns HTTP 403 if wrong role attempts access
  4. Passes permission-scoped context to template (Layer 3 — widget permissions via template tags)
"""
from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin

from backend.apps.dashboard.services import (
    DashboardFactory,
    ROLE_SUPER_ADMIN, ROLE_SCHOOL_ADMIN, ROLE_TEACHER, ROLE_STUDENT,
    ROLE_PARENT, ROLE_FINANCE, ROLE_HR, ROLE_LIBRARIAN, ROLE_WARDEN,
    ROLE_TRANSPORT, ROLE_NURSE, ROLE_EXAM_OFFICER,
)


# ─── RBAC Mixin ─────────────────────────────────────────────────────────────

class RoleRequiredMixin(LoginRequiredMixin):
    """
    Mixin that enforces role-based access at the VIEW level.
    Set `required_role` on the view class.
    Super Admins can access every dashboard.
    """
    required_role: str = None

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        if self.required_role and not DashboardFactory.has_dashboard_access(
            request.user, self.required_role
        ):
            return HttpResponseForbidden(render(request, 'dashboard/403.html', {
                'dashboard_title': 'Access Denied',
                'required_role': self.required_role,
                'user_role': DashboardFactory.resolve_role(request.user),
                'correct_url': DashboardFactory.get_dashboard_url(request.user),
            }))

        return super().dispatch(request, *args, **kwargs)


# ─── Dispatcher (central entry after login) ───────────────────────────────────

class DashboardDispatchView(LoginRequiredMixin, View):
    """
    Central dispatcher — resolve user role and redirect to correct dashboard.
    Called immediately after login by the identity router.
    """
    def get(self, request):
        url = DashboardFactory.get_dashboard_url(request.user)
        return redirect(url)


# ─── Role-Specific Dashboard Views ───────────────────────────────────────────

class SuperAdminDashboardView(RoleRequiredMixin, View):
    required_role = ROLE_SUPER_ADMIN

    def get(self, request):
        ctx = DashboardFactory.get_context(request.user)
        return render(request, 'dashboards/super_admin_dashboard.html', ctx)


class SchoolAdminDashboardView(RoleRequiredMixin, View):
    required_role = ROLE_SCHOOL_ADMIN

    def get(self, request):
        ctx = DashboardFactory.get_context(request.user)
        ctx.update({
            'total_students': 512,
            'total_staff': 48,
            'attendance_rate': 94,
        })
        return render(request, 'dashboards/school_admin_dashboard.html', ctx)


class TeacherDashboardView(RoleRequiredMixin, View):
    required_role = ROLE_TEACHER

    def get(self, request):
        ctx = DashboardFactory.get_context(request.user)
        return render(request, 'dashboards/teacher_dashboard.html', ctx)


class StudentDashboardView(RoleRequiredMixin, View):
    required_role = ROLE_STUDENT

    def get(self, request):
        ctx = DashboardFactory.get_context(request.user)
        return render(request, 'dashboards/student_dashboard.html', ctx)


class ParentDashboardView(RoleRequiredMixin, View):
    required_role = ROLE_PARENT

    def get(self, request):
        ctx = DashboardFactory.get_context(request.user)
        return render(request, 'dashboards/parent_dashboard.html', ctx)


class FinanceDashboardView(RoleRequiredMixin, View):
    required_role = ROLE_FINANCE

    def get(self, request):
        ctx = DashboardFactory.get_context(request.user)
        return render(request, 'dashboards/finance_dashboard.html', ctx)


class HRDashboardView(RoleRequiredMixin, View):
    required_role = ROLE_HR

    def get(self, request):
        ctx = DashboardFactory.get_context(request.user)
        return render(request, 'dashboards/hr_dashboard.html', ctx)


class LibraryDashboardView(RoleRequiredMixin, View):
    required_role = ROLE_LIBRARIAN

    def get(self, request):
        ctx = DashboardFactory.get_context(request.user)
        return render(request, 'dashboards/library_dashboard.html', ctx)


class HostelDashboardView(RoleRequiredMixin, View):
    required_role = ROLE_WARDEN

    def get(self, request):
        ctx = DashboardFactory.get_context(request.user)
        return render(request, 'dashboards/hostel_dashboard.html', ctx)


class TransportDashboardView(RoleRequiredMixin, View):
    required_role = ROLE_TRANSPORT

    def get(self, request):
        ctx = DashboardFactory.get_context(request.user)
        return render(request, 'dashboards/transport_dashboard.html', ctx)


class ClinicDashboardView(RoleRequiredMixin, View):
    required_role = ROLE_NURSE

    def get(self, request):
        ctx = DashboardFactory.get_context(request.user)
        return render(request, 'dashboards/clinic_dashboard.html', ctx)


class ExamDashboardView(RoleRequiredMixin, View):
    required_role = ROLE_EXAM_OFFICER

    def get(self, request):
        ctx = DashboardFactory.get_context(request.user)
        return render(request, 'dashboards/exam_dashboard.html', ctx)
