from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from backend.apps.tenants.models import School
from backend.apps.clinic.models import Clinic, ClinicVisit, SickBayAdmission

class ClinicDashboardWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        schools = School.objects.filter(tenant=getattr(request, 'tenant', None))
        active_school = schools.first()
        
        clinics = Clinic.objects.filter(tenant=getattr(request, 'tenant', None))
        recent_visits = ClinicVisit.objects.filter(tenant=getattr(request, 'tenant', None)).select_related('patient__person')
        active_admissions = SickBayAdmission.objects.filter(tenant=getattr(request, 'tenant', None), discharged_at__isnull=True).select_related('patient__person')
        
        context = {
            'schools': schools,
            'active_school': active_school,
            'clinics': clinics,
            'recent_visits': recent_visits,
            'active_admissions': active_admissions
        }
        return render(request, 'clinic/dashboard.html', context)


class ConsultationDeskWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        visits = ClinicVisit.objects.filter(tenant=getattr(request, 'tenant', None)).select_related('patient__person')
        return render(request, 'clinic/consultation.html', {'visits': visits})
