from django.shortcuts import render, redirect
from django.views import View
from backend.apps.tenants.models import School
from backend.apps.portal.models import PortalProfile, PortalAnnouncement, PortalNotification


def _require_auth(request):
    """Returns redirect response if user is not authenticated, else None."""
    if not request.user.is_authenticated:
        return redirect('login_web')
    return None


def _get_tenant(request):
    return getattr(request, 'tenant', None)


class PortalDashboardWebView(View):
    def get(self, request):
        redir = _require_auth(request)
        if redir:
            return redir

        # Superadmin: send straight to ESSACC
        if request.user.is_superuser:
            return redirect('platform_dashboard_web')

        tenant = _get_tenant(request)
        schools = School.objects.filter(tenant=tenant) if tenant else []
        active_school = schools[0] if schools else None
        announcements = PortalAnnouncement.objects.filter(tenant=tenant) if tenant else []
        notifications = PortalNotification.objects.filter(
            tenant=tenant, user=request.user
        ) if tenant else []

        context = {
            'schools': schools,
            'active_school': active_school,
            'announcements': announcements,
            'notifications': notifications,
        }
        return render(request, 'portal/dashboard.html', context)


class ParentDashboardWebView(View):
    def get(self, request):
        redir = _require_auth(request)
        if redir:
            return redir
        tenant = _get_tenant(request)
        announcements = PortalAnnouncement.objects.filter(
            tenant=tenant, target_role='parent'
        ) if tenant else []
        return render(request, 'portal/parent_dashboard.html', {'announcements': announcements})


class StudentDashboardWebView(View):
    def get(self, request):
        redir = _require_auth(request)
        if redir:
            return redir
        tenant = _get_tenant(request)
        announcements = PortalAnnouncement.objects.filter(
            tenant=tenant, target_role='student'
        ) if tenant else []
        return render(request, 'portal/student_dashboard.html', {'announcements': announcements})


class TeacherDashboardWebView(View):
    def get(self, request):
        redir = _require_auth(request)
        if redir:
            return redir
        tenant = _get_tenant(request)
        announcements = PortalAnnouncement.objects.filter(
            tenant=tenant, target_role='teacher'
        ) if tenant else []
        return render(request, 'portal/teacher_dashboard.html', {'announcements': announcements})
