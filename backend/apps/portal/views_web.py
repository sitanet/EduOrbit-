from django.shortcuts import render, redirect
from django.views import View
from backend.apps.tenants.models import School
from backend.apps.portal.models import PortalProfile, PortalAnnouncement, PortalNotification
from backend.apps.dashboard.services import (
    DashboardFactory,
    ROLE_SCHOOL_ADMIN, ROLE_TEACHER, ROLE_STUDENT, ROLE_PARENT,
)


def _require_auth(request):
    """Returns redirect response if user is not authenticated, else None."""
    if not request.user.is_authenticated:
        return redirect('login_web')
    return None


def _get_tenant(request):
    return getattr(request, 'tenant', None)


class PortalDashboardWebView(View):
    """School Admin portal dashboard — school_admin role only."""

    def get(self, request):
        redir = _require_auth(request)
        if redir:
            return redir

        if not DashboardFactory.has_dashboard_access(request.user, ROLE_SCHOOL_ADMIN):
            return redirect(DashboardFactory.get_dashboard_url(request.user))

        tenant = _get_tenant(request)
        schools = School.objects.filter(tenant=tenant) if tenant else []
        active_school = schools[0] if schools else None
        announcements = PortalAnnouncement.objects.filter(tenant=tenant) if tenant else []
        notifications = PortalNotification.objects.filter(
            tenant=tenant, user=request.user
        ) if tenant else []

        ctx = DashboardFactory.get_context(request.user)
        ctx.update({
            'schools': schools,
            'active_school': active_school,
            'announcements': announcements,
            'notifications': notifications,
        })
        return render(request, 'portal/dashboard.html', ctx)


class ParentDashboardWebView(View):
    """Parent portal — parent/guardian role only."""

    def get(self, request):
        redir = _require_auth(request)
        if redir:
            return redir

        if not DashboardFactory.has_dashboard_access(request.user, ROLE_PARENT):
            return redirect(DashboardFactory.get_dashboard_url(request.user))

        tenant = _get_tenant(request)
        announcements = PortalAnnouncement.objects.filter(
            tenant=tenant, target_role='parent'
        ) if tenant else []
        ctx = DashboardFactory.get_context(request.user)
        ctx['announcements'] = announcements
        return render(request, 'portal/parent_dashboard.html', ctx)


class StudentDashboardWebView(View):
    """Student portal — student role only."""

    def get(self, request):
        redir = _require_auth(request)
        if redir:
            return redir

        if not DashboardFactory.has_dashboard_access(request.user, ROLE_STUDENT):
            return redirect(DashboardFactory.get_dashboard_url(request.user))

        tenant = _get_tenant(request)
        announcements = PortalAnnouncement.objects.filter(
            tenant=tenant, target_role='student'
        ) if tenant else []
        ctx = DashboardFactory.get_context(request.user)
        ctx['announcements'] = announcements
        return render(request, 'portal/student_dashboard.html', ctx)


class TeacherDashboardWebView(View):
    """Teacher portal — teacher role only."""

    def get(self, request):
        redir = _require_auth(request)
        if redir:
            return redir

        if not DashboardFactory.has_dashboard_access(request.user, ROLE_TEACHER):
            return redirect(DashboardFactory.get_dashboard_url(request.user))

        tenant = _get_tenant(request)
        announcements = PortalAnnouncement.objects.filter(
            tenant=tenant, target_role='teacher'
        ) if tenant else []
        ctx = DashboardFactory.get_context(request.user)
        ctx['announcements'] = announcements
        return render(request, 'portal/teacher_dashboard.html', ctx)

