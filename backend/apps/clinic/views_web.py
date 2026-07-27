from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden
from django.views import View
from backend.apps.tenants.models import School
from backend.apps.clinic.models import Clinic, ClinicVisit, SickBayAdmission
from backend.apps.dashboard.services import DashboardFactory, ROLE_NURSE


class ClinicDashboardWebView(View):
    """Clinic dashboard — accessible only by nurse/clinic_staff/doctor roles."""

    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        # Layer 2: Role check
        if not DashboardFactory.has_dashboard_access(request.user, ROLE_NURSE):
            return redirect(DashboardFactory.get_dashboard_url(request.user))

        schools = School.objects.filter(tenant=getattr(request, 'tenant', None))
        active_school = schools.first()

        clinics = Clinic.objects.filter(tenant=getattr(request, 'tenant', None))
        recent_visits = ClinicVisit.objects.filter(
            tenant=getattr(request, 'tenant', None)
        ).select_related('patient__person')
        active_admissions = SickBayAdmission.objects.filter(
            tenant=getattr(request, 'tenant', None),
            discharged_at__isnull=True
        ).select_related('patient__person')

        ctx = DashboardFactory.get_context(request.user)
        ctx.update({
            'schools': schools,
            'active_school': active_school,
            'clinics': clinics,
            'recent_visits': recent_visits,
            'active_admissions': active_admissions,
        })
        return render(request, 'clinic/dashboard.html', ctx)


class ConsultationDeskWebView(View):
    """Consultation desk — accessible only by nurse/clinic_staff/doctor roles."""

    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        if not DashboardFactory.has_dashboard_access(request.user, ROLE_NURSE):
            return redirect(DashboardFactory.get_dashboard_url(request.user))

        visits = ClinicVisit.objects.filter(
            tenant=getattr(request, 'tenant', None)
        ).select_related('patient__person')
        ctx = DashboardFactory.get_context(request.user)
        ctx['visits'] = visits
        return render(request, 'clinic/consultation.html', ctx)

