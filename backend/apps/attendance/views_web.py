from django.shortcuts import render, redirect
from django.views import View
from django.http import HttpResponse
from django.utils import timezone
from backend.apps.tenants.models import School
from backend.apps.people.models import Person
from backend.apps.attendance.models import AttendanceRecord, AttendanceCorrection, AttendanceStatus, AttendanceSession, AttendanceType, AttendanceSource
import datetime

class AttendanceRegisterWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        tenant = getattr(request, 'tenant', None)
        schools = School.objects.filter(tenant=tenant)
        active_school = schools.first()
        
        date_str = request.GET.get('date')
        selected_date = datetime.date.today()
        if date_str:
            try:
                selected_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                pass
                
        session = None
        if active_school:
            att_type, _ = AttendanceType.objects.get_or_create(code="daily", defaults={"name": "Daily Roll Call"})
            session, _ = AttendanceSession.objects.get_or_create(
                school=active_school,
                attendance_type=att_type,
                date=selected_date,
                tenant=tenant
            )
            
        records = AttendanceRecord.objects.filter(
            session=session,
            tenant=tenant
        ).select_related('person', 'status', 'session')
        
        people = Person.objects.filter(tenant=tenant)
        statuses = AttendanceStatus.objects.all()
        
        context = {
            'schools': schools,
            'active_school': active_school,
            'records': records,
            'people': people,
            'statuses': statuses,
            'session': session
        }
        return render(request, 'attendance/register.html', context)

    def post(self, request):
        if not request.user.is_authenticated:
            return HttpResponse("Unauthorized", status=401)
            
        tenant = getattr(request, 'tenant', None)
        person_id = request.POST.get('person_id')
        status_id = request.POST.get('status_id')
        session_id = request.POST.get('session_id')
        
        try:
            person = Person.objects.get(id=person_id, tenant=tenant)
            status = AttendanceStatus.objects.get(id=status_id)
            session = AttendanceSession.objects.get(id=session_id, tenant=tenant)
            source, _ = AttendanceSource.objects.get_or_create(code="manual", defaults={"name": "Manual Input"})
            
            AttendanceRecord.objects.update_or_create(
                session=session,
                person=person,
                tenant=tenant,
                defaults={
                    "status": status,
                    "source": source,
                    "time_marked": timezone.now()
                }
            )
        except Exception as e:
            return HttpResponse(
                f'<div class="p-3 text-xs text-red-800 rounded-lg bg-red-50 dark:bg-slate-900 dark:text-red-400 border border-red-200 dark:border-red-900/30" role="alert">'
                f'<span class="font-semibold">Error:</span> {str(e)}'
                f'</div>'
            )
            
        return HttpResponse(
            '<div class="p-3 text-xs text-emerald-800 rounded-lg bg-emerald-50 dark:bg-slate-900 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-900/30" role="alert">'
            '<span class="font-semibold">Success:</span> Attendance record updated successfully!'
            '</div>'
            '<script>setTimeout(() => { window.location.reload(); }, 1000);</script>'
        )


class AttendanceDashboardWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        corrections = AttendanceCorrection.objects.filter(tenant=getattr(request, 'tenant', None)).select_related('record__person', 'requested_status')
        return render(request, 'attendance/dashboard.html', {'corrections': corrections})
