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

        tenant = getattr(request, 'tenant', None)
        schools = School.objects.filter(tenant=tenant)
        active_school = schools.first()

        from backend.apps.eae.models import Assessment, AssessmentAttempt, Question

        assessments = Assessment.objects.filter(tenant=tenant)
        if active_school:
            assessments = assessments.filter(school=active_school)

        recent_attempts = AssessmentAttempt.objects.filter(tenant=tenant).select_related('student__person', 'assessment')[:10]
        question_count = Question.objects.filter(tenant=tenant).count()

        ctx = DashboardFactory.get_context(request.user)
        ctx.update({
            'schools': schools,
            'active_school': active_school,
            'assessments': assessments,
            'total_assessments': assessments.count(),
            'active_assessments': assessments.filter(is_active=True).count(),
            'question_count': question_count,
            'recent_attempts': recent_attempts,
            'completed_attempts': recent_attempts.count(),
        })
        return render(request, 'eae/dashboard.html', ctx)

    def post(self, request):
        """Handle creating a new CBT assessment."""
        if not request.user.is_authenticated:
            return redirect('login_web')

        tenant = getattr(request, 'tenant', None)
        action = request.POST.get('action')

        if action == 'create_assessment':
            title = request.POST.get('title', '').strip()
            duration = request.POST.get('duration_minutes', 60)
            try:
                dur = int(duration)
            except (ValueError, TypeError):
                dur = 60

            from backend.apps.tenants.models import School
            from backend.apps.eae.models import Assessment

            school = School.objects.filter(tenant=tenant).first()
            if title and school:
                Assessment.objects.create(
                    tenant=tenant,
                    school=school,
                    title=title,
                    duration_minutes=dur,
                    is_active=True
                )

        return redirect('eae_dashboard_web')


class ScheduleExamsWebView(View):
    """Schedule CBT exams and test sessions."""

    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
        tenant = getattr(request, 'tenant', None)
        from backend.apps.eae.models import Assessment
        assessments = Assessment.objects.filter(tenant=tenant)
        ctx = DashboardFactory.get_context(request.user)
        ctx.update({
            'assessments': assessments,
            'total_scheduled': assessments.count(),
        })
        return render(request, 'eae/schedule.html', ctx)

    def post(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
        tenant = getattr(request, 'tenant', None)
        action = request.POST.get('action')
        if action == 'add_exam':
            title = request.POST.get('title', '').strip()
            duration = request.POST.get('duration_minutes', 60)
            try:
                dur = int(duration)
            except (ValueError, TypeError):
                dur = 60
            from backend.apps.tenants.models import School
            from backend.apps.eae.models import Assessment
            school = School.objects.filter(tenant=tenant).first()
            if title and school:
                Assessment.objects.create(
                    tenant=tenant,
                    school=school,
                    title=title,
                    duration_minutes=dur,
                    is_active=True
                )
        return redirect('eae_schedule_web')


class QuestionBankWebView(View):
    """Question Bank repository and items management."""

    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
        tenant = getattr(request, 'tenant', None)
        from backend.apps.eae.models import Question
        from backend.apps.academic.models import Subject
        questions = Question.objects.filter(tenant=tenant).select_related('subject')
        subjects = Subject.objects.filter(tenant=tenant)
        ctx = DashboardFactory.get_context(request.user)
        ctx.update({
            'questions': questions,
            'subjects': subjects,
            'total_questions': questions.count(),
        })
        return render(request, 'eae/questions.html', ctx)

    def post(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
        tenant = getattr(request, 'tenant', None)
        action = request.POST.get('action')
        if action == 'add_question':
            subject_id = request.POST.get('subject_id')
            topic = request.POST.get('topic', 'General').strip()
            q_text = request.POST.get('question_text', '').strip()
            q_type = request.POST.get('question_type', 'mcq')
            from backend.apps.academic.models import Subject
            from backend.apps.tenants.models import School
            from backend.apps.eae.models import Question
            school = School.objects.filter(tenant=tenant).first()
            subject = Subject.objects.filter(id=subject_id, tenant=tenant).first() if subject_id else Subject.objects.filter(tenant=tenant).first()
            if q_text and school and subject:
                Question.objects.create(
                    tenant=tenant,
                    school=school,
                    subject=subject,
                    topic=topic or 'General',
                    question_text=q_text,
                    question_type=q_type,
                    status='published'
                )
        return redirect('eae_questions_web')


class CBTConsoleWebView(View):
    """Live CBT proctored examination monitor."""

    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
        tenant = getattr(request, 'tenant', None)
        from backend.apps.eae.models import AssessmentAttempt, Assessment
        attempts = AssessmentAttempt.objects.filter(tenant=tenant).select_related('student__person', 'assessment')[:15]
        assessments = Assessment.objects.filter(tenant=tenant, is_active=True)
        ctx = DashboardFactory.get_context(request.user)
        ctx.update({
            'attempts': attempts,
            'assessments': assessments,
            'active_students': attempts.filter(status='started').count(),
        })
        return render(request, 'eae/cbt.html', ctx)


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

