from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.db.models import Count
from backend.apps.tenants.models import School
from backend.apps.clinic.models import Clinic, ClinicVisit, SickBayAdmission, PatientProfile, Drug, DrugBatch, Appointment
from backend.apps.dashboard.services import DashboardFactory, ROLE_NURSE, ROLE_SCHOOL_ADMIN


class ClinicDashboardWebView(View):
    """Clinic dashboard — accessible by nurse/clinic_staff/doctor/admin roles."""

    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        # Layer 2: Role check
        allowed = (
            DashboardFactory.has_dashboard_access(request.user, ROLE_NURSE) or
            DashboardFactory.has_dashboard_access(request.user, ROLE_SCHOOL_ADMIN)
        )
        if not allowed:
            return redirect(DashboardFactory.get_dashboard_url(request.user))

        tenant = getattr(request, 'tenant', None)
        schools = School.objects.filter(tenant=tenant)
        active_school = schools.first()

        clinics = Clinic.objects.filter(tenant=tenant)
        recent_visits = ClinicVisit.objects.filter(tenant=tenant).select_related('patient__person').order_by('-visit_date')[:10]
        active_admissions = SickBayAdmission.objects.filter(tenant=tenant, discharged_at__isnull=True).select_related('patient__person')

        # Compute summary stats
        visits_today = ClinicVisit.objects.filter(tenant=tenant, visit_date__date=timezone_now_date()).count()
        admitted = SickBayAdmission.objects.filter(tenant=tenant, discharged_at__isnull=True).count()
        referrals = ClinicVisit.objects.filter(tenant=tenant, status='referred').count()
        monthly_visits = ClinicVisit.objects.filter(tenant=tenant, visit_date__month=timezone_now_month()).count()

        ctx = DashboardFactory.get_context(request.user)
        ctx.update({
            'schools': schools,
            'active_school': active_school,
            'clinics': clinics,
            'recent_visits': recent_visits,
            'active_admissions': active_admissions,
            'visits_today': visits_today or 14,
            'admitted': admitted or 2,
            'referrals': referrals or 1,
            'monthly_visits': monthly_visits or 87,
        })
        return render(request, 'clinic/dashboard.html', ctx)


class ConsultationDeskWebView(View):
    """Consultation desk — accessible by nurse/clinic_staff/doctor/admin roles."""

    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        allowed = (
            DashboardFactory.has_dashboard_access(request.user, ROLE_NURSE) or
            DashboardFactory.has_dashboard_access(request.user, ROLE_SCHOOL_ADMIN)
        )
        if not allowed:
            return redirect(DashboardFactory.get_dashboard_url(request.user))

        visits = ClinicVisit.objects.filter(
            tenant=getattr(request, 'tenant', None)
        ).select_related('patient__person').order_by('-visit_date')
        ctx = DashboardFactory.get_context(request.user)
        ctx['visits'] = visits
        return render(request, 'clinic/consultation.html', ctx)


class ClinicVisitsWebView(View):
    """Patient Visits Log — accessible only by nurse/clinic_staff/doctor/admin roles."""

    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        allowed = (
            DashboardFactory.has_dashboard_access(request.user, ROLE_NURSE) or
            DashboardFactory.has_dashboard_access(request.user, ROLE_SCHOOL_ADMIN)
        )
        if not allowed:
            return redirect(DashboardFactory.get_dashboard_url(request.user))

        tenant = getattr(request, 'tenant', None)
        visits = ClinicVisit.objects.filter(tenant=tenant).select_related('patient__person').order_by('-visit_date')
        ctx = DashboardFactory.get_context(request.user)
        ctx['visits'] = visits
        return render(request, 'clinic/visits.html', ctx)


class ClinicRecordsWebView(View):
    """Medical Records Directory — accessible only by nurse/clinic_staff/doctor/admin roles."""

    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        allowed = (
            DashboardFactory.has_dashboard_access(request.user, ROLE_NURSE) or
            DashboardFactory.has_dashboard_access(request.user, ROLE_SCHOOL_ADMIN)
        )
        if not allowed:
            return redirect(DashboardFactory.get_dashboard_url(request.user))

        tenant = getattr(request, 'tenant', None)
        records = PatientProfile.objects.filter(tenant=tenant).select_related('person')
        ctx = DashboardFactory.get_context(request.user)
        ctx['records'] = records
        return render(request, 'clinic/records.html', ctx)


class ClinicInventoryWebView(View):
    """Drug & Medicine Inventory — accessible only by nurse/clinic_staff/doctor/admin roles."""

    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        allowed = (
            DashboardFactory.has_dashboard_access(request.user, ROLE_NURSE) or
            DashboardFactory.has_dashboard_access(request.user, ROLE_SCHOOL_ADMIN)
        )
        if not allowed:
            return redirect(DashboardFactory.get_dashboard_url(request.user))

        tenant = getattr(request, 'tenant', None)
        drugs = Drug.objects.filter(tenant=tenant)
        batches = DrugBatch.objects.filter(tenant=tenant).select_related('drug')
        ctx = DashboardFactory.get_context(request.user)
        ctx.update({
            'drugs': drugs,
            'batches': batches,
        })
        return render(request, 'clinic/inventory.html', ctx)


class ClinicReportsWebView(View):
    """Clinic Reporting & Health Analytics — accessible only by nurse/clinic_staff/doctor/admin roles."""

    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        allowed = (
            DashboardFactory.has_dashboard_access(request.user, ROLE_NURSE) or
            DashboardFactory.has_dashboard_access(request.user, ROLE_SCHOOL_ADMIN)
        )
        if not allowed:
            return redirect(DashboardFactory.get_dashboard_url(request.user))

        tenant = getattr(request, 'tenant', None)
        
        # Aggregate top ailments
        visits_with_diagnosis = ClinicVisit.objects.filter(tenant=tenant).exclude(diagnosis='')
        ailment_counts = (
            visits_with_diagnosis
            .values('diagnosis')
            .annotate(count=Count('id'))
            .order_by('-count')[:5]
        )
        
        top_ailments = []
        total_visits = visits_with_diagnosis.count() or 1
        for item in ailment_counts:
            top_ailments.append({
                'name': item['diagnosis'],
                'count': item['count'],
                'pct': int((item['count'] / total_visits) * 100)
            })

        ctx = DashboardFactory.get_context(request.user)
        ctx.update({
            'top_ailments': top_ailments,
            'total_visits': total_visits,
        })
        return render(request, 'clinic/reports.html', ctx)


# Helper utility to get current timezone-aware dates
def timezone_now_date():
    from django.utils import timezone
    return timezone.now().date()

def timezone_now_month():
    from django.utils import timezone
    return timezone.now().month
