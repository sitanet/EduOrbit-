from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from backend.apps.tenants.models import School
from backend.apps.transport.models import Vehicle, Route, Trip

class TransportDashboardWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        schools = School.objects.filter(tenant=getattr(request, 'tenant', None))
        active_school = schools.first()
        
        vehicles = Vehicle.objects.filter(tenant=getattr(request, 'tenant', None))
        active_trips = Trip.objects.filter(tenant=getattr(request, 'tenant', None), status='in_progress').select_related('route', 'vehicle', 'driver__person')
        
        context = {
            'schools': schools,
            'active_school': active_school,
            'vehicles': vehicles,
            'active_trips': active_trips
        }
        return render(request, 'transport/dashboard.html', context)


class RoutesPlannerWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        routes = Route.objects.filter(tenant=getattr(request, 'tenant', None)).prefetch_related('stops')
        return render(request, 'transport/routes.html', {'routes': routes})
