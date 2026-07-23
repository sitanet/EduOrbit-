from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from backend.apps.tenants.models import School
from backend.apps.facilities.models import Building, WorkOrder, UtilityMeter

class FacilitiesDashboardWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        schools = School.objects.filter(tenant=getattr(request, 'tenant', None))
        active_school = schools.first()
        
        buildings = Building.objects.filter(tenant=getattr(request, 'tenant', None))
        active_orders = WorkOrder.objects.filter(tenant=getattr(request, 'tenant', None)).exclude(status='closed').select_related('request__room__floor__building')
        utility_meters = UtilityMeter.objects.filter(tenant=getattr(request, 'tenant', None)).select_related('building')
        
        context = {
            'schools': schools,
            'active_school': active_school,
            'buildings': buildings,
            'active_orders': active_orders,
            'utility_meters': utility_meters
        }
        return render(request, 'facilities/dashboard.html', context)


class WorkOrdersBoardWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        orders = WorkOrder.objects.filter(tenant=getattr(request, 'tenant', None)).select_related('request__room__floor__building')
        return render(request, 'facilities/board.html', {'orders': orders})
