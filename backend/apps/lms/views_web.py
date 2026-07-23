from django.shortcuts import render, redirect
from django.views import View
from backend.apps.tenants.models import School
from backend.apps.lms.models import LearningModule, Badge, StudentBadge

class LMSDashboardWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        tenant = getattr(request, 'tenant', None)
        schools = School.objects.filter(tenant=tenant)
        active_school = schools.first()
        
        modules = LearningModule.objects.filter(school=active_school, tenant=tenant).select_related('subject')
        badges = Badge.objects.all()
        
        if hasattr(request.user, 'person_profile') and hasattr(request.user.person_profile, 'student_profile'):
            student = request.user.person_profile.student_profile
            earned_badges = StudentBadge.objects.filter(student=student, tenant=tenant).select_related('student__person', 'badge')
        else:
            earned_badges = StudentBadge.objects.filter(tenant=tenant).select_related('student__person', 'badge')
            
        context = {
            'schools': schools,
            'active_school': active_school,
            'modules': modules,
            'badges': badges,
            'earned_badges': earned_badges
        }
        return render(request, 'lms/dashboard.html', context)


from backend.apps.academic.models import Subject
from django.http import HttpResponse

class ModuleBuilderWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        tenant = getattr(request, 'tenant', None)
        modules = LearningModule.objects.filter(tenant=tenant).select_related('subject')
        subjects = Subject.objects.filter(tenant=tenant)
        return render(request, 'lms/module_builder.html', {
            'modules': modules,
            'subjects': subjects
        })

    def post(self, request):
        if not request.user.is_authenticated:
            return HttpResponse("Unauthorized", status=401)
            
        tenant = getattr(request, 'tenant', None)
        schools = School.objects.filter(tenant=tenant)
        active_school = schools.first()
        
        title = request.POST.get('title')
        topic = request.POST.get('topic', '')
        subject_id = request.POST.get('subject_id')
        version = request.POST.get('version', 1)
        
        try:
            subject = Subject.objects.get(id=subject_id, tenant=tenant)
            LearningModule.objects.create(
                tenant=tenant,
                school=active_school,
                subject=subject,
                title=title,
                topic=topic,
                version=int(version)
            )
        except Exception as e:
            return HttpResponse(
                f'<div class="p-3 text-xs text-red-800 rounded-lg bg-red-50 dark:bg-slate-900 dark:text-red-400 border border-red-200 dark:border-red-900/30" role="alert">'
                f'<span class="font-semibold">Error:</span> {str(e)}'
                f'</div>'
            )
            
        return HttpResponse(
            '<div class="p-3 text-xs text-emerald-800 rounded-lg bg-emerald-50 dark:bg-slate-900 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-900/30" role="alert">'
            '<span class="font-semibold">Success:</span> Course module created successfully!'
            '</div>'
            '<script>setTimeout(() => { window.location.reload(); }, 1000);</script>'
        )
