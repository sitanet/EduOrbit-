from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from backend.apps.tenants.models import School
from backend.apps.transport.models import Vehicle, Route, Trip
from backend.apps.dashboard.services import DashboardFactory, ROLE_TRANSPORT, ROLE_SCHOOL_ADMIN


class TransportDashboardWebView(View):
    """Transport dashboard — transport_officer, transport_manager, school_admin, superuser only."""

    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        allowed = (
            DashboardFactory.has_dashboard_access(request.user, ROLE_TRANSPORT) or
            DashboardFactory.has_dashboard_access(request.user, ROLE_SCHOOL_ADMIN)
        )
        if not allowed:
            return redirect(DashboardFactory.get_dashboard_url(request.user))

        schools = School.objects.filter(tenant=getattr(request, 'tenant', None))
        active_school = schools.first()
        vehicles = Vehicle.objects.filter(tenant=getattr(request, 'tenant', None))
        active_trips = Trip.objects.filter(
            tenant=getattr(request, 'tenant', None), status='in_progress'
        ).select_related('route', 'vehicle', 'driver__person')

        ctx = DashboardFactory.get_context(request.user)
        ctx.update({
            'schools': schools,
            'active_school': active_school,
            'vehicles': vehicles,
            'active_trips': active_trips,
        })
        return render(request, 'transport/dashboard.html', ctx)


class RoutesPlannerWebView(View):
    """Routes planner — transport_officer/school_admin roles only."""

    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        allowed = (
            DashboardFactory.has_dashboard_access(request.user, ROLE_TRANSPORT) or
            DashboardFactory.has_dashboard_access(request.user, ROLE_SCHOOL_ADMIN)
        )
        if not allowed:
            return redirect(DashboardFactory.get_dashboard_url(request.user))

        routes = Route.objects.filter(
            tenant=getattr(request, 'tenant', None)
        ).prefetch_related('stops')
        ctx = DashboardFactory.get_context(request.user)
        ctx['routes'] = routes
        return render(request, 'transport/routes.html', ctx)

