from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from backend.apps.tenants.models import School
from backend.apps.emrp.models import Examination, ExamResult

class EMRPDashboardWebView(View):
    """EMRP Admin Dashboard — exam_officer, academic_admin, and school_admin roles."""

    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        tenant = getattr(request, 'tenant', None)
        from backend.apps.tenants.models import School
        from backend.apps.emrp.models import Examination, ExamResult

        schools = School.objects.filter(tenant=tenant)
        active_school = schools.first()
        exams = Examination.objects.filter(tenant=tenant)
        results = ExamResult.objects.filter(tenant=tenant)

        from backend.apps.dashboard.services import DashboardFactory
        ctx = DashboardFactory.get_context(request.user)
        ctx.update({
            'schools': schools,
            'active_school': active_school,
            'exams': exams,
            'total_exams': exams.count(),
            'total_results': results.count(),
        })
        return render(request, 'emrp/dashboard.html', ctx)

    def post(self, request):
        """Handle creating a new exam session."""
        if not request.user.is_authenticated:
            return redirect('login_web')

        tenant = getattr(request, 'tenant', None)
        action = request.POST.get('action')

        if action == 'create_exam':
            name = request.POST.get('name', '').strip()
            from backend.apps.tenants.models import School
            from backend.apps.emrp.models import Examination

            school = School.objects.filter(tenant=tenant).first()
            if name and school:
                Examination.objects.create(
                    tenant=tenant,
                    school=school,
                    name=name
                )

        return redirect('emrp_dashboard_web')


class BroadsheetWebView(View):
    def get(self, request, exam_id):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        exam = get_object_or_404(Examination, id=exam_id, tenant=getattr(request, 'tenant', None))
        results = ExamResult.objects.filter(exam=exam, tenant=getattr(request, 'tenant', None)).select_related('student__person')
        
        context = {
            'exam': exam,
            'results': results
        }
        return render(request, 'emrp/broadsheet.html', context)


class ReportsBroadsheetWebView(View):
    """Terminal Report Cards & Broadsheets — academic, exam_officer, school_admin."""

    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
        tenant = getattr(request, 'tenant', None)
        from backend.apps.emrp.models import Examination, ExamResult
        exams = Examination.objects.filter(tenant=tenant)
        results = ExamResult.objects.filter(tenant=tenant).select_related('student__person', 'exam')[:20]
        context = {
            'exams': exams,
            'results': results,
            'total_reports': results.count(),
        }
        return render(request, 'emrp/reports.html', context)
