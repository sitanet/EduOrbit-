from django.shortcuts import render, redirect
from django.views import View
from django.http import HttpResponse
from backend.apps.people.models import StudentProfile
from backend.apps.students.models import StudentPortfolio, StudentTimeline
from backend.apps.dashboard.views_web import RoleRequiredMixin
from backend.apps.dashboard.services import ROLE_STUDENT, ROLE_TEACHER, ROLE_SCHOOL_ADMIN

class StudentPortfolioWebView(RoleRequiredMixin, View):
    required_roles = [ROLE_STUDENT, ROLE_TEACHER, ROLE_SCHOOL_ADMIN]

    def get(self, request):
            
        tenant = getattr(request, 'tenant', None)
        portfolios = StudentPortfolio.objects.filter(tenant=tenant).select_related('student__person')
        students = StudentProfile.objects.filter(tenant=tenant).select_related('person')
        return render(request, 'students/portfolio.html', {
            'portfolios': portfolios,
            'students': students
        })

    def post(self, request):
        if not request.user.is_authenticated:
            return HttpResponse("Unauthorized", status=401)
            
        tenant = getattr(request, 'tenant', None)
        student_id = request.POST.get('student_id')
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        date_earned = request.POST.get('date_earned')
        
        try:
            student = StudentProfile.objects.get(id=student_id, tenant=tenant)
            StudentPortfolio.objects.create(
                tenant=tenant,
                student=student,
                title=title,
                description=description,
                date_earned=date_earned
            )
            StudentTimeline.objects.create(
                tenant=tenant,
                student=student,
                event_type="achievement",
                title=f"Awarded: {title}",
                description=description
            )
        except Exception as e:
            return HttpResponse(
                f'<div class="p-3 text-xs text-red-800 rounded-lg bg-red-50 dark:bg-slate-900 dark:text-red-400 border border-red-200 dark:border-red-900/30" role="alert">'
                f'<span class="font-semibold">Error:</span> {str(e)}'
                f'</div>'
            )
            
        return HttpResponse(
            '<div class="p-3 text-xs text-emerald-800 rounded-lg bg-emerald-50 dark:bg-slate-900 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-900/30" role="alert">'
            '<span class="font-semibold">Success:</span> Portfolio achievement logged successfully!'
            '</div>'
            '<script>setTimeout(() => { window.location.reload(); }, 1000);</script>'
        )


class StudentTimelineWebView(RoleRequiredMixin, View):
    required_roles = [ROLE_STUDENT, ROLE_TEACHER, ROLE_SCHOOL_ADMIN]

    def get(self, request):
        tenant = getattr(request, 'tenant', None)
        student_id = request.GET.get('student_id')
        
        if student_id:
            timelines = StudentTimeline.objects.filter(student_id=student_id, tenant=tenant).select_related('student__person')
        else:
            timelines = StudentTimeline.objects.filter(tenant=tenant).select_related('student__person')
            
        return render(request, 'students/timeline.html', {
            'timelines': timelines,
            'selected_student_id': student_id
        })
