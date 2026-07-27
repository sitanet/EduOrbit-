from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from backend.apps.tenants.models import School
from backend.apps.eae.models import Assessment, AssessmentAttempt, AttemptAnswer
from backend.apps.dashboard.services import (
    DashboardFactory, ROLE_EXAM_OFFICER, ROLE_SCHOOL_ADMIN,
    ROLE_TEACHER, ROLE_STUDENT,
)


class EAEDashboardWebView(View):
    """EAE admin dashboard — exam_officer and school_admin roles only."""

    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        allowed = (
            DashboardFactory.has_dashboard_access(request.user, ROLE_EXAM_OFFICER) or
            DashboardFactory.has_dashboard_access(request.user, ROLE_SCHOOL_ADMIN)
        )
        if not allowed:
            return redirect(DashboardFactory.get_dashboard_url(request.user))

        schools = School.objects.filter(tenant=getattr(request, 'tenant', None))
        active_school = schools.first()
        assessments = Assessment.objects.filter(
            school=active_school, tenant=getattr(request, 'tenant', None)
        )
        recent_attempts = AssessmentAttempt.objects.filter(
            assessment__school=active_school,
            tenant=getattr(request, 'tenant', None)
        ).select_related('student__person', 'assessment')

        ctx = DashboardFactory.get_context(request.user)
        ctx.update({
            'schools': schools,
            'active_school': active_school,
            'assessments': assessments,
            'recent_attempts': recent_attempts,
        })
        return render(request, 'eae/dashboard.html', ctx)


class CBTAttemptWebView(View):
    """CBT attempt screen — teachers, students, and exam officers only."""

    def get(self, request, attempt_id):
        if not request.user.is_authenticated:
            return redirect('login_web')

        allowed = (
            DashboardFactory.has_dashboard_access(request.user, ROLE_EXAM_OFFICER) or
            DashboardFactory.has_dashboard_access(request.user, ROLE_TEACHER) or
            DashboardFactory.has_dashboard_access(request.user, ROLE_STUDENT) or
            DashboardFactory.has_dashboard_access(request.user, ROLE_SCHOOL_ADMIN)
        )
        if not allowed:
            return redirect(DashboardFactory.get_dashboard_url(request.user))

        attempt = get_object_or_404(
            AssessmentAttempt, id=attempt_id,
            tenant=getattr(request, 'tenant', None)
        )
        answers = AttemptAnswer.objects.filter(attempt=attempt).select_related('question')
        ctx = DashboardFactory.get_context(request.user)
        ctx.update({'attempt': attempt, 'answers': answers})
        return render(request, 'eae/attempt_screen.html', ctx)

