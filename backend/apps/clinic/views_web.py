from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.http import JsonResponse
from django.db.models import Q, Count
from django.db import models
from backend.apps.tenants.models import School
from backend.apps.clinic.models import Clinic, ClinicVisit, SickBayAdmission, PatientProfile, Drug, DrugBatch, Appointment, DrugDispenseLog, Ward
from backend.apps.dashboard.services import DashboardFactory, ROLE_NURSE, ROLE_SCHOOL_ADMIN

# Helper utility to get current timezone-aware dates
def timezone_now_date():
    from django.utils import timezone
    return timezone.now().date()

def timezone_now_month():
    from django.utils import timezone
    return timezone.now().month


class PatientSearchJsonView(View):
    """
    Live patient/student name search endpoint for the consultation modal autocomplete.
    Searches the core Person registry (students, staff) so any person in the school can be found.
    GET /clinic/patients/search/?q=john
    """
    def get(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({'results': []}, status=401)

        q = request.GET.get('q', '').strip()
        tenant = getattr(request, 'tenant', None)

        if len(q) < 1:
            return JsonResponse({'results': []})

        from backend.apps.people.models import Person

        # Search core Person registry (students, teachers, staff)
        person_qs = Person.objects.filter(
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Q(person_number__icontains=q)
        )
        if tenant:
            person_qs = person_qs.filter(tenant=tenant)

        persons = person_qs.select_related('patient_profile')[:10]

        results = []
        for p in persons:
            # Retrieve or create PatientProfile for this person
            patient_profile, _ = PatientProfile.objects.get_or_create(
                tenant=tenant or p.tenant,
                person=p
            )
            results.append({
                'id': str(patient_profile.id),
                'name': f"{p.first_name} {p.last_name}",
                'person_number': p.person_number or '—',
                'blood_group': patient_profile.blood_group or '—',
            })

        return JsonResponse({'results': results})



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
            'visits_today': visits_today,
            'admitted': admitted,
            'referrals': referrals,
            'monthly_visits': monthly_visits,
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

    def post(self, request):
        """Log a new patient visit from consultation desk."""
        if not request.user.is_authenticated:
            return redirect('login_web')

        allowed = (
            DashboardFactory.has_dashboard_access(request.user, ROLE_NURSE) or
            DashboardFactory.has_dashboard_access(request.user, ROLE_SCHOOL_ADMIN)
        )
        if not allowed:
            return redirect(DashboardFactory.get_dashboard_url(request.user))

        tenant = getattr(request, 'tenant', None)
        action = request.POST.get('action')

        if action == 'log_visit':
            patient_id = request.POST.get('patient_id', '').strip()
            patient_name = request.POST.get('patient_name', '').strip()
            symptoms = request.POST.get('symptoms', '').strip()
            diagnosis = request.POST.get('diagnosis', '').strip()
            status = request.POST.get('status', 'completed')

            patient = None
            if patient_id:
                patient = PatientProfile.objects.filter(id=patient_id, tenant=tenant).first()

            if not patient and patient_name:
                # Try finding patient profile by name
                parts = patient_name.split(maxsplit=1)
                first_name = parts[0]
                last_name = parts[1] if len(parts) > 1 else ''

                patient = PatientProfile.objects.filter(
                    tenant=tenant,
                    person__first_name__icontains=first_name
                ).first()

                if not patient:
                    # Create Person and PatientProfile if completely new
                    from backend.apps.people.models import Person
                    person = Person.objects.create(
                        tenant=tenant,
                        first_name=first_name,
                        last_name=last_name or 'Patient'
                    )
                    patient = PatientProfile.objects.create(
                        tenant=tenant,
                        person=person
                    )

            if patient and symptoms:
                ClinicVisit.objects.create(
                    tenant=tenant,
                    patient=patient,
                    symptoms=symptoms,
                    diagnosis=diagnosis,
                    status=status
                )

                if status == 'admitted':
                    ward, _ = Ward.objects.get_or_create(
                        tenant=tenant,
                        name='General Ward'
                    )
                    active_count = SickBayAdmission.objects.filter(tenant=tenant, discharged_at__isnull=True).count()
                    bed_num = f"B-{active_count + 1:02d}"

                    SickBayAdmission.objects.create(
                        tenant=tenant,
                        patient=patient,
                        ward=ward,
                        bed_number=bed_num
                    )

        return redirect('consultation_desk_web')


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

        from django.utils import timezone
        today = timezone.now().date()
        tenant = getattr(request, 'tenant', None)
        drugs = Drug.objects.filter(tenant=tenant)
        batches = DrugBatch.objects.filter(tenant=tenant).select_related('drug')
        dispense_logs = DrugDispenseLog.objects.filter(tenant=tenant).select_related('drug').order_by('-dispensed_at')[:30]

        ctx = DashboardFactory.get_context(request.user)
        ctx.update({
            'drugs': drugs,
            'batches': batches,
            'dispense_logs': dispense_logs,
            'total_dispensed_today': sum(l.quantity for l in dispense_logs if l.dispensed_at.date() == today) if dispense_logs else 0,
        })
        return render(request, 'clinic/inventory.html', ctx)

    def post(self, request):
        """Handle Add Drug / Restock form submission from the pharmacy page."""
        if not request.user.is_authenticated:
            return redirect('login_web')

        action = request.POST.get('action')
        tenant = getattr(request, 'tenant', None)

        if action == 'add_drug':
            drug_name = request.POST.get('drug_name', '').strip()
            stock_qty = request.POST.get('stock_qty', 0)
            batch_number = request.POST.get('batch_number', '').strip()
            expiry_date = request.POST.get('expiry_date', '').strip()

            if drug_name:
                drug, created = Drug.objects.get_or_create(
                    tenant=tenant,
                    name=drug_name,
                    defaults={'stock_qty': 0}
                )
                try:
                    drug.stock_qty += int(stock_qty)
                except (ValueError, TypeError):
                    pass
                drug.save()

                # Optionally create a batch record if batch details provided
                if batch_number and expiry_date:
                    from datetime import datetime
                    try:
                        exp = datetime.strptime(expiry_date, '%Y-%m-%d').date()
                        DrugBatch.objects.create(
                            tenant=tenant,
                            drug=drug,
                            batch_number=batch_number,
                            expiry_date=exp,
                        )
                    except ValueError:
                        pass  # Ignore bad date gracefully

        elif action == 'dispense_drug':
            drug_id = request.POST.get('drug_id')
            dispense_qty = request.POST.get('dispense_qty', 1)
            dispensed_to = request.POST.get('dispensed_to', '').strip() or request.POST.get('patient_name', '').strip()
            notes = request.POST.get('notes', '').strip()
            try:
                qty = int(dispense_qty)
            except (ValueError, TypeError):
                qty = 1

            if drug_id and qty > 0:
                drug = Drug.objects.filter(id=drug_id, tenant=tenant).first()
                if drug:
                    drug.stock_qty = max(0, drug.stock_qty - qty)
                    drug.save()

                    # Log dispense transaction for audit report
                    DrugDispenseLog.objects.create(
                        tenant=tenant,
                        drug=drug,
                        dispensed_to=dispensed_to,
                        quantity=qty,
                        notes=notes
                    )

        # Redirect back to pharmacy page after POST (PRG pattern)
        return redirect(request.path)


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


class SickBayWebView(View):
    """Sick Bay Admissions — active in-patients with ward and bed detail."""

    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        allowed = (
            DashboardFactory.has_dashboard_access(request.user, ROLE_NURSE) or
            DashboardFactory.has_dashboard_access(request.user, ROLE_SCHOOL_ADMIN)
        )
        if not allowed:
            return redirect(DashboardFactory.get_dashboard_url(request.user))

        from django.utils import timezone
        tenant = getattr(request, 'tenant', None)

        # Backfill/sync any ClinicVisit with status='admitted' that hasn't been added to SickBayAdmission
        admitted_visits = ClinicVisit.objects.filter(tenant=tenant, status='admitted').select_related('patient')
        for v in admitted_visits:
            if v.patient and not SickBayAdmission.objects.filter(tenant=tenant, patient=v.patient, discharged_at__isnull=True).exists():
                ward, _ = Ward.objects.get_or_create(tenant=tenant, name='General Ward')
                count = SickBayAdmission.objects.filter(tenant=tenant, discharged_at__isnull=True).count()
                SickBayAdmission.objects.create(
                    tenant=tenant,
                    patient=v.patient,
                    ward=ward,
                    bed_number=f"B-{count + 1:02d}"
                )

        active_admissions = SickBayAdmission.objects.filter(
            tenant=tenant, discharged_at__isnull=True
        ).select_related('patient__person', 'ward').order_by('-admitted_at')

        discharged_today = SickBayAdmission.objects.filter(
            tenant=tenant,
            discharged_at__date=timezone.now().date()
        ).count()

        ctx = DashboardFactory.get_context(request.user)
        ctx.update({
            'active_admissions': active_admissions,
            'active_count': active_admissions.count(),
            'discharged_today': discharged_today,
        })
        return render(request, 'clinic/sickbay.html', ctx)

    def post(self, request):
        """Handle patient discharge from sick bay."""
        if not request.user.is_authenticated:
            return redirect('login_web')

        tenant = getattr(request, 'tenant', None)
        action = request.POST.get('action')

        if action == 'discharge':
            admission_id = request.POST.get('admission_id')
            if admission_id:
                from django.utils import timezone
                SickBayAdmission.objects.filter(
                    id=admission_id, tenant=tenant
                ).update(discharged_at=timezone.now())

        return redirect('clinic_sickbay_web')
