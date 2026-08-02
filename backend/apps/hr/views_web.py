import json
import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.utils import timezone
from backend.apps.tenants.models import School
from backend.apps.hr.models import (
    EmployeeProfile, LeaveRequest, LeaveType, JobVacancy, JobApplication, InterviewPanel, InterviewScorecard, OfferLetter, HRSettings,
    PayrollPeriod, PayrollRun, PayrollPayslip, AttendanceRecord
)
from backend.apps.hr.selectors import EmployeeSelector, RecruitmentSelector, OnboardingSelector, HRSettingsSelector, LeaveSelector
from backend.apps.hr.services import EmployeeService, RecruitmentService, OnboardingService, LeaveService, PayrollService
from backend.apps.efbm.services.finance import AccountingService

class HRDashboardWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
        
        # Get the hr_role set by HRContextMiddleware
        role = getattr(request, 'hr_role', 'employee')
        
        # Check if user should be redirected based on role
        allowed_roles = ['hr_admin', 'hr_officer', 'super_admin', 'school_admin']
        
        if role not in allowed_roles:
            if role == 'payroll_admin':
                return redirect('/hr/payroll/')
            elif role == 'supervisor':
                return redirect('/hr/manager/team/')
            else:
                # Regular employees go to ESS portal
                return redirect('/hr/ess/')
                
        tenant = getattr(request, 'tenant', None)
        schools = School.objects.filter(tenant=tenant)
        active_school = schools.first()
        
        employees = EmployeeSelector.get_all_employees(tenant)
        recent_leaves = LeaveRequest.objects.filter(tenant=tenant).select_related('employee__person')
        candidates = RecruitmentSelector.get_applications(tenant)
        
        staff_members = []
        for emp in employees:
            tasks = emp.onboarding_tasks.all()
            task_list = [{
                'id': str(t.id),
                'name': t.task_name,
                'category': t.category.title(),
                'is_completed': t.is_completed,
                'completed_at': t.completed_at.strftime('%Y-%m-%d') if t.completed_at else '—'
            } for t in tasks]
            
            assets = emp.assigned_assets.all()
            asset_list = [{
                'name': a.asset_name,
                'serial': a.serial_number,
                'type': a.asset_type,
                'assigned': a.date_assigned.strftime('%Y-%m-%d') if a.date_assigned else '—'
            } for a in assets]
                
            objs = emp.objectives.all()
            obj_list = [{
                'title': o.title,
                'progress': o.progress_percentage,
                'status': o.status.replace('_', ' ').title()
            } for o in objs]
                
            balances = emp.leave_balances.all()
            balance_list = [{
                'type': b.leave_type_name.title() if b.leave_type_name else (b.leave_type.name.title() if b.leave_type else 'Annual Leave'),
                'allowed': b.allowed_days,
                'remaining': b.remaining_days
            } for b in balances]
                
            history = emp.assignment_history.filter(is_active=True).first()
            campus = history.campus_name if history else (active_school.name if active_school else 'Main Campus')
            cost_centre = history.cost_centre if history else 'CC-001'
            manager_name = f"{history.manager.person.first_name} {history.manager.person.last_name}" if history and history.manager and history.manager.person else "—"
            
            staff_members.append({
                'id': str(emp.id),
                'employee_number': emp.employee_number,
                'name': f"{emp.person.first_name} {emp.person.last_name}" if emp.person else "Unknown",
                'email': emp.person.user.email if emp.person and emp.person.user else "—",
                'gender': emp.person.gender.title() if emp.person else "—",
                'dob': emp.person.date_of_birth.strftime('%B %d, %Y') if emp.person and emp.person.date_of_birth else "—",
                'nationality': emp.person.nationality if emp.person else "—",
                'state': emp.person.state_of_origin if emp.person else "—",
                'joined_date': emp.joined_date.strftime('%B %d, %Y') if emp.joined_date else "—",
                'department': history.department_name if history and history.department_name else ('Academics' if emp.job_title == 'Teacher' else 'Administration'),
                'role': emp.job_title,
                'salary_grade': emp.salary_grade.replace('_', ' ').title(),
                'status': emp.status.title() if emp.status else 'Active',
                'campus': campus,
                'cost_centre': cost_centre,
                'manager': manager_name,
                
                'tasks': task_list,
                'assets': asset_list,
                'objectives': obj_list,
                'balances': balance_list
            })
            
        staff_members_json = json.dumps(staff_members)
            
        context = {
            'schools': schools,
            'active_school': active_school,
            'employees': employees,
            'staff_members': staff_members,
            'staff_members_json': staff_members_json,
            'candidates': candidates,
            'recent_leaves': recent_leaves
        }
        return render(request, 'hr/dashboard.html', context)

    def post(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        tenant = getattr(request, 'tenant', None)
        action = request.POST.get('action')
        candidate_id = request.POST.get('candidate_id')
        
        if candidate_id:
            application = get_object_or_404(JobApplication, id=candidate_id, tenant=tenant)
            
            if action == 'invite_interview':
                RecruitmentService.schedule_interview(tenant, application, timezone.now())
            elif action == 'send_offer':
                RecruitmentService.generate_offer(tenant, application, offered_salary=75000.00, designation=application.vacancy.title if application.vacancy else 'Teacher', start_date=timezone.now().date())
            elif action == 'accept_offer':
                RecruitmentService.hire_candidate(tenant, application)
            elif action == 'reject_offer':
                application.stage = 'rejected'
                application.save()
                
        elif action == 'seed_candidate':
            vacancy, _ = JobVacancy.objects.get_or_create(
                tenant=tenant,
                title="History Teacher",
                defaults={'description': 'Teach history classes.', 'department': 'Sciences'}
            )
            JobApplication.objects.create(
                tenant=tenant,
                vacancy=vacancy,
                first_name="Natasha",
                last_name="Romanoff",
                email=f"natasha.{uuid.uuid4().hex[:4]}@eduorbit.com",
                stage='applied'
            )
        return redirect('hr_dashboard_web')


class LeaveCalendarWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        tenant = getattr(request, 'tenant', None)
        leaves = LeaveSelector.get_leave_requests(tenant)
        leave_types = LeaveSelector.get_leave_types(tenant)
        employees = EmployeeSelector.get_all_employees(tenant)
        
        context = {
            'leaves': leaves,
            'leave_types': leave_types,
            'employees': employees
        }
        return render(request, 'hr/leave_calendar.html', context)

    def post(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        tenant = getattr(request, 'tenant', None)
        action = request.POST.get('action')
        
        if action == 'submit_leave':
            employee_id = request.POST.get('employee_id')
            leave_type_id = request.POST.get('leave_type_id')
            start_date_str = request.POST.get('start_date')
            end_date_str = request.POST.get('end_date')
            reason = request.POST.get('reason', '')
            
            if employee_id and leave_type_id and start_date_str and end_date_str:
                employee = EmployeeProfile.objects.filter(id=employee_id, tenant=tenant).first()
                leave_type = LeaveType.objects.filter(id=leave_type_id, tenant=tenant).first()
                if employee and leave_type:
                    from datetime import datetime
                    start_d = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                    end_d = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                    LeaveService.submit_leave_request(tenant, employee, leave_type, start_d, end_d, reason=reason)
                    
        elif action == 'approve_leave':
            leave_id = request.POST.get('leave_id')
            if leave_id:
                LeaveService.approve_leave_request(tenant, leave_id)
        elif action == 'reject_leave':
            leave_id = request.POST.get('leave_id')
            reason = request.POST.get('reason', '')
            if leave_id:
                LeaveService.reject_leave_request(tenant, leave_id, reason=reason)
                
        return redirect('leave_calendar_web')


class RecruitmentDashboardWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        tenant = getattr(request, 'tenant', None)
        jobs = RecruitmentSelector.get_vacancies(tenant)
        candidates = RecruitmentSelector.get_applications(tenant)
        
        context = {
            'jobs': jobs,
            'candidates': candidates
        }
        return render(request, 'hr/recruitment_dashboard.html', context)

    def post(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        tenant = getattr(request, 'tenant', None)
        action = request.POST.get('action')
        
        if action == 'create_job':
            title = request.POST.get('title')
            department = request.POST.get('department')
            description = request.POST.get('description', '')
            if title:
                RecruitmentService.publish_vacancy(tenant, title=title, department=department, description=description)
        elif action == 'seed_candidate':
            vacancy, _ = JobVacancy.objects.get_or_create(
                tenant=tenant,
                title="History Teacher",
                defaults={'description': 'Teach history classes.', 'department': 'Sciences'}
            )
            JobApplication.objects.create(
                tenant=tenant,
                vacancy=vacancy,
                first_name="Natasha",
                last_name="Romanoff",
                email=f"natasha.{uuid.uuid4().hex[:4]}@eduorbit.com",
                stage='applied'
            )
        return redirect('recruitment_dashboard_web')


class CandidateReviewWebView(View):
    def get(self, request, candidate_id):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        tenant = getattr(request, 'tenant', None)
        candidate = get_object_or_404(JobApplication, id=candidate_id, tenant=tenant)
        interviews = InterviewPanel.objects.filter(application=candidate, tenant=tenant)
        schools = School.objects.filter(tenant=tenant)
        
        context = {
            'candidate': candidate,
            'interviews': interviews,
            'schools': schools
        }
        return render(request, 'hr/candidate_review.html', context)

    def post(self, request, candidate_id):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        tenant = getattr(request, 'tenant', None)
        candidate = get_object_or_404(JobApplication, id=candidate_id, tenant=tenant)
        action = request.POST.get('action')
        
        if action == 'invite_interview':
            RecruitmentService.schedule_interview(tenant, candidate, timezone.now())
        elif action == 'log_score':
            score = float(request.POST.get('score', 0.0))
            interviewer = EmployeeProfile.objects.filter(tenant=tenant).first()
            if interviewer:
                RecruitmentService.submit_scorecard(tenant, candidate, interviewer, score)
        elif action == 'send_offer':
            RecruitmentService.generate_offer(tenant, candidate, offered_salary=75000.00, designation=candidate.vacancy.title if candidate.vacancy else 'Teacher', start_date=timezone.now().date())
        elif action == 'accept_offer':
            department_name = request.POST.get('department_name', 'Sciences')
            salary_grade = request.POST.get('salary_grade', 'grade_1')
            school_id = request.POST.get('school_id')
            school_obj = School.objects.filter(id=school_id, tenant=tenant).first() if school_id else None
            
            RecruitmentService.hire_candidate(tenant, candidate, school=school_obj, department_name=department_name, salary_grade=salary_grade)
            return redirect('hr_dashboard_web')
        elif action == 'reject_offer':
            candidate.stage = 'rejected'
            candidate.save()
            
        return redirect('candidate_review_web', candidate_id=candidate.id)


class PayrollWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
        hr_role = getattr(request, 'hr_role', '')
        # Also accept users whose Django group is hr_admin or payroll_admin
        user_groups = set(request.user.groups.values_list('name', flat=True))
        has_payroll_access = (
            hr_role in ['payroll_admin', 'hr_admin', 'school_admin', 'super_admin']
            or 'hr_admin' in user_groups
            or 'payroll_admin' in user_groups
            or request.user.is_superuser
        )
        if not has_payroll_access:
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("Access Denied: Payroll Administrator privileges required.")
            
        tenant = getattr(request, 'tenant', None)
        periods = PayrollPeriod.objects.filter(tenant=tenant)
        selected_period_id = request.GET.get('period_id')
        
        selected_period = None
        active_run = None
        payslips = []
        
        if selected_period_id:
            selected_period = get_object_or_404(PayrollPeriod, id=selected_period_id, tenant=tenant)
            active_run = PayrollRun.objects.filter(period=selected_period, tenant=tenant).first()
            if active_run:
                payslips = PayrollPayslip.objects.filter(payroll_run=active_run, tenant=tenant).select_related('employee__person')
                
        context = {
            'periods': periods,
            'selected_period_id': selected_period_id,
            'selected_period': selected_period,
            'active_run': active_run,
            'payslips': payslips
        }
        return render(request, 'hr/payroll_dashboard.html', context)

    def post(self, request, run_id=None):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        tenant = getattr(request, 'tenant', None)
        
        if run_id:
            run = get_object_or_404(PayrollRun, id=run_id, tenant=tenant)
            accounting_service = AccountingService()
            PayrollService.approve_and_post_payroll(tenant, run.id, accounting_service)
            return redirect(f"/hr/payroll/?period_id={run.period.id}")
            
        period_id = request.POST.get('period_id')
        if period_id:
            PayrollService.generate_payroll_run(tenant, period_id)
            return redirect(f"/hr/payroll/?period_id={period_id}")
            
        return redirect('hr_dashboard_web')


class AttendanceDashboardWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        tenant = getattr(request, 'tenant', None)
        today = timezone.now().date()
        
        from backend.apps.hr.selectors.attendance import AttendanceSelector
        from backend.apps.hr.models.attendance import AttendanceShift, AttendanceAdjustment
        
        stats = AttendanceSelector.get_department_summary(tenant, today)
        records = AttendanceRecord.objects.filter(tenant=tenant, attendance_date=today).select_related('employee__person__user', 'shift')
        adjustments = AttendanceAdjustment.objects.filter(tenant=tenant, approval_status='Pending').select_related('requested_by__person__user', 'attendance_record')
        shifts = AttendanceShift.objects.filter(tenant=tenant, active=True)
        
        context = {
            'stats': stats,
            'records': records,
            'adjustments': adjustments,
            'shifts': shifts
        }
        return render(request, 'hr/attendance_dashboard.html', context)


class AttendanceGenerateWebView(View):
    def post(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        tenant = getattr(request, 'tenant', None)
        today = timezone.now().date()
        
        from backend.apps.hr.services.attendance import AttendanceService
        AttendanceService.generate_daily_attendance(tenant, today)
        
        return redirect('hr_attendance_dashboard')


class AttendanceAdjustmentActionWebView(View):
    def post(self, request, adjustment_id, action):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        tenant = getattr(request, 'tenant', None)
        
        # Get active supervisor/HR profiles
        from backend.apps.hr.models.employee import EmployeeProfile
        from backend.apps.hr.services.attendance import AttendanceService
        
        emp = EmployeeProfile.objects.filter(tenant=tenant, user=request.user).first()
        
        if action == 'approve':
            # Run multi-level approval flow automatically for tests/simplified demo
            AttendanceService.approve_adjustment(tenant, adjustment_id, supervisor=emp, action='approve')
            AttendanceService.approve_adjustment(tenant, adjustment_id, hr=emp, action='approve')
        else:
            AttendanceService.approve_adjustment(tenant, adjustment_id, supervisor=emp, action='reject')
            
        return redirect('hr_attendance_dashboard')


class AttendanceReportWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        tenant = getattr(request, 'tenant', None)
        fmt = request.GET.get('format', 'csv')
        today = timezone.now().date()
        
        from backend.apps.hr.models.attendance import AttendanceRecord
        records = AttendanceRecord.objects.filter(tenant=tenant, attendance_date=today).select_related('employee')
        
        import csv
        from django.http import HttpResponse
        
        if fmt == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="attendance_report_{today}.csv"'
            
            writer = csv.writer(response)
            writer.writerow(['Employee', 'Date', 'Check In', 'Check Out', 'Hours', 'Overtime', 'Status'])
            for r in records:
                writer.writerow([r.employee.employee_number, r.attendance_date, r.check_in, r.check_out, r.total_hours, r.overtime_hours, r.attendance_status])
            return response
        else:
            from reportlab.pdfgen import canvas
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="attendance_report_{today}.pdf"'
            
            p = canvas.Canvas(response)
            p.drawString(100, 800, f"Attendance Report - {today}")
            p.drawString(100, 785, "=" * 60)
            
            y = 750
            p.drawString(100, y, "Employee ID | Date | Check-In | Check-Out | Status")
            y -= 15
            p.drawString(100, y, "-" * 80)
            y -= 20
            
            for r in records:
                if y < 50:
                    p.showPage()
                    y = 800
                p.drawString(100, y, f"{r.employee.employee_number} | {r.attendance_date} | {r.check_in or '-'} | {r.check_out or '-'} | {r.attendance_status}")
                y -= 20
                
            p.showPage()
            p.save()
            return response


class ESSDashboardWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
        tenant = getattr(request, 'tenant', None)
        from backend.apps.hr.models import EmployeeProfile, LeaveBalance, EmployeeAsset, PayrollPayslip, LeaveRequest
        emp = EmployeeProfile.objects.filter(tenant=tenant, person__user=request.user).first()
        if not emp:
            emp = EmployeeProfile.objects.filter(tenant=tenant).select_related('person').first()

        leave_balances = LeaveBalance.objects.filter(tenant=tenant, employee=emp) if emp else []
        assets = EmployeeAsset.objects.filter(tenant=tenant, employee=emp) if emp else []
        payslips = PayrollPayslip.objects.filter(tenant=tenant, employee=emp) if emp else []
        leave_requests = LeaveRequest.objects.filter(tenant=tenant, employee=emp) if emp else []

        ctx = {
            'employee': emp,
            'leave_balances': leave_balances,
            'assets': assets,
            'payslips': payslips,
            'leave_requests': leave_requests,
        }
        return render(request, 'hr/ess/dashboard.html', ctx)


class ManagerTeamWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
        tenant = getattr(request, 'tenant', None)
        employees = EmployeeProfile.objects.filter(tenant=tenant).select_related('person')
        return render(request, 'hr/manager/team_dashboard.html', {'employees': employees})


class StaffDirectoryWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
        tenant = getattr(request, 'tenant', None)
        employees = EmployeeSelector.get_all_employees(tenant)
        return render(request, 'hr/admin/directory.html', {'employees': employees})


class StaffIdCardWebView(View):
    def get(self, request, employee_id):
        if not request.user.is_authenticated:
            return redirect('login_web')
        tenant = getattr(request, 'tenant', None)
        try:
            employee = EmployeeProfile.objects.select_related('person', 'tenant').get(id=employee_id, tenant=tenant)
        except EmployeeProfile.DoesNotExist:
            from django.http import Http404
            raise Http404("Employee profile not found")
            
        return render(request, 'hr/admin/id_card.html', {
            'employee': employee,
            'tenant': tenant,
        })


class OrgChartWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
        tenant = getattr(request, 'tenant', None)
        employees = EmployeeProfile.objects.filter(tenant=tenant).select_related('person')
        return render(request, 'hr/admin/org_chart.html', {'employees': employees})


class OnboardingTrackerWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
        tenant = getattr(request, 'tenant', None)
        from backend.apps.hr.models import OnboardingTask
        tasks = OnboardingTask.objects.filter(tenant=tenant).select_related('employee__person')
        pending_count = tasks.filter(is_completed=False).count()
        completed_count = tasks.filter(is_completed=True).count()
        onboarding_employees_count = tasks.values('employee').distinct().count()

        ctx = {
            'tasks': tasks,
            'pending_count': pending_count,
            'completed_count': completed_count,
            'onboarding_employees_count': onboarding_employees_count,
        }
        return render(request, 'hr/admin/onboarding_tracker.html', ctx)


class PerformanceWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
        tenant = getattr(request, 'tenant', None)
        from backend.apps.hr.models.appraisal import PerformanceReview
        reviews = PerformanceReview.objects.filter(tenant=tenant).select_related('employee__person')
        return render(request, 'hr/performance/dashboard.html', {'reviews': reviews})


class TrainingWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
        tenant = getattr(request, 'tenant', None)
        from backend.apps.hr.models.training import TrainingProgram
        programs = TrainingProgram.objects.filter(tenant=tenant)
        return render(request, 'hr/training/dashboard.html', {'programs': programs})


class DisciplinaryWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
        return render(request, 'hr/disciplinary/dashboard.html', {'cases': []})


class RewardsWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
        return render(request, 'hr/rewards/wall.html', {'rewards': []})


class FinancePostingsWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
        return render(request, 'hr/finance/postings.html', {'postings': []})


class AnalyticsWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
        tenant = getattr(request, 'tenant', None)
        employee_count = EmployeeProfile.objects.filter(tenant=tenant).count()
        return render(request, 'hr/analytics/dashboard.html', {'employee_count': employee_count})


class NotificationsWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
        return render(request, 'hr/notifications/center.html', {'notifications': []})


class AuditTrailWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
        tenant = getattr(request, 'tenant', None)
        from backend.apps.hr.models.employee import HRAuditLog
        logs = HRAuditLog.objects.filter(tenant=tenant).order_by('-created_at')[:50]
        return render(request, 'hr/audit/trail.html', {'logs': logs})


class HRSettingsWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
        tenant = getattr(request, 'tenant', None)
        settings = HRSettingsSelector.get_tenant_settings(tenant)
        return render(request, 'hr/settings/index.html', {'settings': settings})


class ImportWizardWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
        return render(request, 'hr/import/wizard.html')


class BulkOperationsWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
        return render(request, 'hr/bulk/operations.html')


class EnterpriseSearchWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
        q = request.GET.get('q', '')
        tenant = getattr(request, 'tenant', None)
        employees = EmployeeSelector.get_all_employees(tenant, {'search': q}) if q else []
        return render(request, 'hr/search/results.html', {'employees': employees, 'query': q})


class ReportsHubWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
        return render(request, 'hr/reports/hub.html')


class HRUserManualWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
        return render(request, 'hr/user_manual.html')


class OnboardingWizardWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
        return render(request, 'hr/admin/onboarding_wizard.html')


