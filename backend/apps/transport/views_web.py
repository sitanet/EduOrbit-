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

        tenant = getattr(request, 'tenant', None)
        schools = School.objects.filter(tenant=tenant)
        active_school = schools.first()

        from backend.apps.transport.models import Route, Vehicle, Driver, Trip, TransportSubscription

        vehicles = Vehicle.objects.filter(tenant=tenant)
        routes = Route.objects.filter(tenant=tenant)
        drivers = Driver.objects.filter(tenant=tenant).select_related('person')
        active_trips = Trip.objects.filter(tenant=tenant).select_related('route', 'vehicle', 'driver__person')[:10]
        total_passengers = TransportSubscription.objects.filter(tenant=tenant).count()

        ctx = DashboardFactory.get_context(request.user)
        ctx.update({
            'schools': schools,
            'active_school': active_school,
            'vehicles': vehicles,
            'routes': routes,
            'drivers': drivers,
            'active_trips': active_trips,
            'total_vehicles': vehicles.count(),
            'total_routes': routes.count(),
            'total_drivers': drivers.count(),
            'total_passengers': total_passengers,
            'in_maintenance': vehicles.filter(status='maintenance').count(),
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

        tenant = getattr(request, 'tenant', None)
        from backend.apps.transport.models import Route, RouteStop, Trip

        routes = Route.objects.filter(
            tenant=tenant
        ).prefetch_related('stops', 'trips')

        total_stops = RouteStop.objects.filter(tenant=tenant).count()
        active_trips = Trip.objects.filter(tenant=tenant, status='in_progress').count()
        total_distance = sum(float(r.total_distance_km or 0) for r in routes) if routes else 0

        ctx = DashboardFactory.get_context(request.user)
        ctx.update({
            'routes': routes,
            'total_routes': routes.count(),
            'total_stops': total_stops,
            'active_trips': active_trips,
            'total_distance': round(total_distance, 1),
        })
        return render(request, 'transport/routes.html', ctx)

    def post(self, request):
        """Handle adding a new transport route."""
        if not request.user.is_authenticated:
            return redirect('login_web')

        tenant = getattr(request, 'tenant', None)
        action = request.POST.get('action')

        if action == 'add_route':
            name = request.POST.get('name', '').strip()
            start_point = request.POST.get('start_point', '').strip()
            end_point = request.POST.get('end_point', '').strip()
            distance = request.POST.get('total_distance_km', 0.0)

            try:
                dist = float(distance)
            except (ValueError, TypeError):
                dist = 0.0

            from backend.apps.transport.models import Route, RouteStop

            if name and start_point and end_point:
                route = Route.objects.create(
                    tenant=tenant,
                    name=name,
                    start_point=start_point,
                    end_point=end_point,
                    total_distance_km=dist
                )
                # Auto-generate initial origin and terminal stops
                RouteStop.objects.create(tenant=tenant, route=route, stop_name=start_point, stop_order=1)
                RouteStop.objects.create(tenant=tenant, route=route, stop_name=end_point, stop_order=2)

        return redirect('routes_planner_web')


class VehiclesFleetWebView(View):
    """Vehicles & Bus Fleet Inventory — transport_officer/school_admin roles."""

    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
        allowed = (
            DashboardFactory.has_dashboard_access(request.user, ROLE_TRANSPORT) or
            DashboardFactory.has_dashboard_access(request.user, ROLE_SCHOOL_ADMIN)
        )
        if not allowed:
            return redirect(DashboardFactory.get_dashboard_url(request.user))

        tenant = getattr(request, 'tenant', None)
        from backend.apps.transport.models import Vehicle
        vehicles = Vehicle.objects.filter(tenant=tenant)
        ctx = DashboardFactory.get_context(request.user)
        ctx.update({
            'vehicles': vehicles,
            'total_vehicles': vehicles.count(),
            'active_vehicles': vehicles.filter(status='active').count(),
            'maintenance_vehicles': vehicles.filter(status='maintenance').count(),
        })
        return render(request, 'transport/vehicles.html', ctx)

    def post(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
        tenant = getattr(request, 'tenant', None)
        action = request.POST.get('action')
        if action == 'add_vehicle':
            reg_num = request.POST.get('registration_number', '').strip()
            plate_num = request.POST.get('plate_number', '').strip()
            capacity = request.POST.get('capacity', 30)
            try:
                cap = int(capacity)
            except (ValueError, TypeError):
                cap = 30
            from backend.apps.transport.models import Vehicle
            if reg_num and plate_num:
                Vehicle.objects.create(
                    tenant=tenant,
                    registration_number=reg_num,
                    plate_number=plate_num,
                    capacity=cap,
                    status='active'
                )
        return redirect('vehicles_fleet_web')


class DriversDirectoryWebView(View):
    """Drivers Directory — transport_officer/school_admin roles."""

    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
        allowed = (
            DashboardFactory.has_dashboard_access(request.user, ROLE_TRANSPORT) or
            DashboardFactory.has_dashboard_access(request.user, ROLE_SCHOOL_ADMIN)
        )
        if not allowed:
            return redirect(DashboardFactory.get_dashboard_url(request.user))

        tenant = getattr(request, 'tenant', None)
        from backend.apps.transport.models import Driver
        drivers = Driver.objects.filter(tenant=tenant).select_related('person')
        ctx = DashboardFactory.get_context(request.user)
        ctx.update({
            'drivers': drivers,
            'total_drivers': drivers.count(),
        })
        return render(request, 'transport/drivers.html', ctx)

    def post(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
        tenant = getattr(request, 'tenant', None)
        action = request.POST.get('action')
        if action == 'add_driver':
            name = request.POST.get('driver_name', '').strip()
            license_num = request.POST.get('license_number', '').strip()
            if name:
                parts = name.split(maxsplit=1)
                fn = parts[0]
                ln = parts[1] if len(parts) > 1 else 'Driver'
                from backend.apps.people.models import Person
                from backend.apps.transport.models import Driver
                person = Person.objects.create(tenant=tenant, first_name=fn, last_name=ln)
                Driver.objects.create(tenant=tenant, person=person, license_number=license_num or 'LIC-PENDING')
        return redirect('drivers_directory_web')


class PassengersManifestWebView(View):
    """Passengers & Student Bus Subscriptions — transport_officer/school_admin roles."""

    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
        allowed = (
            DashboardFactory.has_dashboard_access(request.user, ROLE_TRANSPORT) or
            DashboardFactory.has_dashboard_access(request.user, ROLE_SCHOOL_ADMIN)
        )
        if not allowed:
            return redirect(DashboardFactory.get_dashboard_url(request.user))

        tenant = getattr(request, 'tenant', None)
        from backend.apps.transport.models import TransportSubscription, Route
        subs = TransportSubscription.objects.filter(tenant=tenant).select_related('student', 'route', 'stop')
        routes = Route.objects.filter(tenant=tenant)
        ctx = DashboardFactory.get_context(request.user)
        ctx.update({
            'subscriptions': subs,
            'routes': routes,
            'total_passengers': subs.count(),
        })
        return render(request, 'transport/passengers.html', ctx)


class VehicleMaintenanceWebView(View):
    """Vehicle Maintenance & Servicing Logs — transport_officer/school_admin roles."""

    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
        allowed = (
            DashboardFactory.has_dashboard_access(request.user, ROLE_TRANSPORT) or
            DashboardFactory.has_dashboard_access(request.user, ROLE_SCHOOL_ADMIN)
        )
        if not allowed:
            return redirect(DashboardFactory.get_dashboard_url(request.user))

        tenant = getattr(request, 'tenant', None)
        from backend.apps.transport.models import MaintenanceSchedule, Vehicle, FuelLog
        schedules = MaintenanceSchedule.objects.filter(tenant=tenant).select_related('vehicle')
        fuel_logs = FuelLog.objects.filter(tenant=tenant).select_related('vehicle')
        vehicles = Vehicle.objects.filter(tenant=tenant)
        ctx = DashboardFactory.get_context(request.user)
        ctx.update({
            'schedules': schedules,
            'fuel_logs': fuel_logs,
            'vehicles': vehicles,
        })
        return render(request, 'transport/maintenance.html', ctx)

    def post(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
        tenant = getattr(request, 'tenant', None)
        action = request.POST.get('action')
        if action == 'add_maintenance':
            vehicle_id = request.POST.get('vehicle_id')
            desc = request.POST.get('description', '').strip()
            date = request.POST.get('scheduled_date', '').strip()
            from backend.apps.transport.models import MaintenanceSchedule, Vehicle
            from django.utils import timezone
            vehicle = Vehicle.objects.filter(id=vehicle_id, tenant=tenant).first()
            if vehicle and desc:
                MaintenanceSchedule.objects.create(
                    tenant=tenant,
                    vehicle=vehicle,
                    description=desc,
                    scheduled_date=date or timezone.now().date(),
                    status='scheduled'
                )
        return redirect('vehicle_maintenance_web')


class TransportReportsWebView(View):
    """Transport Fleet & Route Performance Reports — transport_officer/school_admin roles."""

    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
        allowed = (
            DashboardFactory.has_dashboard_access(request.user, ROLE_TRANSPORT) or
            DashboardFactory.has_dashboard_access(request.user, ROLE_SCHOOL_ADMIN)
        )
        if not allowed:
            return redirect(DashboardFactory.get_dashboard_url(request.user))

        tenant = getattr(request, 'tenant', None)
        from backend.apps.transport.models import Route, Vehicle, Trip
        routes = Route.objects.filter(tenant=tenant)
        vehicles = Vehicle.objects.filter(tenant=tenant)
        trips = Trip.objects.filter(tenant=tenant).select_related('route', 'vehicle')
        ctx = DashboardFactory.get_context(request.user)
        ctx.update({
            'routes': routes,
            'vehicles': vehicles,
            'trips': trips,
            'total_trips': trips.count(),
        })
        return render(request, 'transport/reports.html', ctx)

