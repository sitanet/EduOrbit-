from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from backend.apps.tenants.models import School
from backend.apps.hostel.models import Hostel, HostelRoom, BedAllocation
from backend.apps.dashboard.services import DashboardFactory, ROLE_WARDEN, ROLE_SCHOOL_ADMIN


class HostelDashboardWebView(View):
    """Hostel dashboard — warden, hostel_officer, school_admin, superuser only."""

    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        allowed = (
            DashboardFactory.has_dashboard_access(request.user, ROLE_WARDEN) or
            DashboardFactory.has_dashboard_access(request.user, ROLE_SCHOOL_ADMIN)
        )
        if not allowed:
            return redirect(DashboardFactory.get_dashboard_url(request.user))

        schools = School.objects.filter(tenant=getattr(request, 'tenant', None))
        active_school = schools.first()
        hostels = Hostel.objects.filter(tenant=getattr(request, 'tenant', None))
        allocations = BedAllocation.objects.filter(
            tenant=getattr(request, 'tenant', None), status='active'
        ).select_related('bed__room__block__hostel', 'student')

        ctx = DashboardFactory.get_context(request.user)
        ctx.update({
            'schools': schools,
            'active_school': active_school,
            'hostels': hostels,
            'allocations': allocations,
        })
        return render(request, 'hostel/dashboard.html', ctx)


class RoomsDirectoryWebView(View):
    """Rooms directory — warden/hostel_officer/school_admin roles only."""

    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        allowed = (
            DashboardFactory.has_dashboard_access(request.user, ROLE_WARDEN) or
            DashboardFactory.has_dashboard_access(request.user, ROLE_SCHOOL_ADMIN)
        )
        if not allowed:
            return redirect(DashboardFactory.get_dashboard_url(request.user))

        rooms = HostelRoom.objects.filter(
            tenant=getattr(request, 'tenant', None)
        ).select_related('block__hostel').prefetch_related('beds')
        ctx = DashboardFactory.get_context(request.user)
        ctx['rooms'] = rooms
        return render(request, 'hostel/rooms.html', ctx)

