from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from backend.apps.tenants.models import School
from backend.apps.eae.models import Assessment, AssessmentAttempt, AttemptAnswer

class EAEDashboardWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        schools = School.objects.filter(tenant=getattr(request, 'tenant', None))
        active_school = schools.first()
        
        assessments = Assessment.objects.filter(school=active_school, tenant=getattr(request, 'tenant', None))
        recent_attempts = AssessmentAttempt.objects.filter(assessment__school=active_school, tenant=getattr(request, 'tenant', None)).select_related('student__person', 'assessment')
        
        context = {
            'schools': schools,
            'active_school': active_school,
            'assessments': assessments,
            'recent_attempts': recent_attempts
        }
        return render(request, 'eae/dashboard.html', context)


class CBTAttemptWebView(View):
    def get(self, request, attempt_id):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        attempt = get_object_or_404(AssessmentAttempt, id=attempt_id, tenant=getattr(request, 'tenant', None))
        answers = AttemptAnswer.objects.filter(attempt=attempt).select_related('question')
        
        context = {
            'attempt': attempt,
            'answers': answers
        }
        return render(request, 'eae/attempt_screen.html', context)
