from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from backend.apps.tenants.models import School
from backend.apps.hostel.models import Hostel, HostelRoom, BedAllocation

class HostelDashboardWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        schools = School.objects.filter(tenant=getattr(request, 'tenant', None))
        active_school = schools.first()
        
        hostels = Hostel.objects.filter(tenant=getattr(request, 'tenant', None))
        allocations = BedAllocation.objects.filter(tenant=getattr(request, 'tenant', None), status='active').select_related('bed__room__block__hostel', 'student')
        
        context = {
            'schools': schools,
            'active_school': active_school,
            'hostels': hostels,
            'allocations': allocations
        }
        return render(request, 'hostel/dashboard.html', context)


class RoomsDirectoryWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        rooms = HostelRoom.objects.filter(tenant=getattr(request, 'tenant', None)).select_related('block__hostel').prefetch_related('beds')
        return render(request, 'hostel/rooms.html', {'rooms': rooms})
