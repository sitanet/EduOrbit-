from django.shortcuts import render, redirect
from django.views import View
from django.http import HttpResponse
from django.utils import timezone
from datetime import timedelta
from backend.apps.tenants.models import School
from backend.apps.academic.models import AcademicYear, EducationLevel, AcademicClass, Subject
from backend.apps.dashboard.views_web import RoleRequiredMixin
from backend.apps.dashboard.services import ROLE_SCHOOL_ADMIN, ROLE_TEACHER

class AcademicWizardWebView(RoleRequiredMixin, View):
    required_role = ROLE_SCHOOL_ADMIN

    def get(self, request):
            
        schools = School.objects.filter(tenant=getattr(request, 'tenant', None))
        return render(request, 'academic/setup_wizard.html', {'schools': schools})

    def post(self, request):
        # Stepper onboarding wizard configuration loader
        school_id = request.POST.get('school_id')
        year_name = request.POST.get('year_name')
        year_code = request.POST.get('year_code')
        
        try:
            school = School.objects.get(id=school_id, tenant=getattr(request, 'tenant', None))
            # Provision active AcademicYear for this school
            year = AcademicYear.objects.create(
                school=school,
                tenant=getattr(request, 'tenant', None),
                name=year_name,
                code=year_code,
                start_date=timezone.now().date(),
                end_date=(timezone.now() + timedelta(days=365)).date(),
                status='active'
            )
        except Exception as e:
            return HttpResponse(
                f'<div class="p-4 mb-4 text-sm text-red-800 rounded-xl bg-red-50 dark:bg-slate-900 dark:text-red-400 border border-red-200 dark:border-red-900/30" role="alert">'
                f'<span class="font-semibold">Failed initializing academic structure:</span> {str(e)}'
                f'</div>'
            )

        return HttpResponse(
            '<div class="p-4 mb-4 text-sm text-emerald-800 rounded-xl bg-emerald-50 dark:bg-slate-900 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-900/30" role="alert">'
            '<h3 class="font-bold text-base mb-1">Academic Foundation Setup Complete!</h3>'
            '<p>Schools setup complete. Redirecting...</p>'
            '</div>'
            '<script>setTimeout(() => { window.location.href = "/academic/dashboard/"; }, 2000);</script>'
        )


class AcademicDashboardWebView(RoleRequiredMixin, View):
    required_roles = [ROLE_SCHOOL_ADMIN]

    def get(self, request):
        schools = School.objects.filter(tenant=getattr(request, 'tenant', None))
        active_school = schools.first()
        
        years = AcademicYear.objects.filter(school=active_school) if active_school else []
        classes = AcademicClass.objects.filter(tenant=getattr(request, 'tenant', None))[:10]
        subjects = Subject.objects.filter(school=active_school) if active_school else []
        
        context = {
            'schools': schools,
            'active_school': active_school,
            'years': years,
            'classes': classes,
            'subjects': subjects
        }
        return render(request, 'academic/dashboard.html', context)


class SubjectManagementWebView(RoleRequiredMixin, View):
    required_roles = [ROLE_SCHOOL_ADMIN, ROLE_TEACHER]

    def get(self, request):
        tenant = getattr(request, 'tenant', None)
        schools = School.objects.filter(tenant=tenant)
        active_school = schools.first()
        
        # Ensure a default Curriculum exists
        from backend.apps.academic.models import Curriculum, Subject
        curriculum, _ = Curriculum.objects.get_or_create(
            code='national-curriculum',
            defaults={
                'name': 'National Standard Curriculum',
                'version': '1.0.0',
                'description': 'Standard state educational guidelines.'
            }
        )
        
        subjects = Subject.objects.filter(school=active_school) if active_school else []
        
        from backend.apps.academic.models import SubjectCategory
        custom_categories = SubjectCategory.objects.filter(school=active_school)
        
        context = {
            'schools': schools,
            'active_school': active_school,
            'subjects': subjects,
            'custom_categories': custom_categories,
            'curriculum': curriculum
        }
        return render(request, 'academic/subjects.html', context)

    def post(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        action = request.POST.get('action')
        tenant = getattr(request, 'tenant', None)
        
        if action == 'create':
            name = request.POST.get('name')
            code = request.POST.get('code')
            category = request.POST.get('category', 'core')
            credit_units = request.POST.get('credit_units', 1)
            school_id = request.POST.get('school_id')
            
            school = School.objects.filter(id=school_id, tenant=tenant).first() if school_id else School.objects.filter(tenant=tenant).first()
            
            from backend.apps.academic.models import Curriculum, Subject
            curriculum = Curriculum.objects.filter(code='national-curriculum').first()
            if not curriculum:
                curriculum = Curriculum.objects.create(
                    name='National Standard Curriculum',
                    code='national-curriculum'
                )
                
            if name and code and school:
                Subject.objects.get_or_create(
                    tenant=tenant,
                    school=school,
                    code=code,
                    defaults={
                        'curriculum': curriculum,
                        'name': name,
                        'category': category,
                        'credit_units': int(credit_units)
                    }
                )
        elif action == 'create_category':
            name = request.POST.get('name')
            code = request.POST.get('code')
            school_id = request.POST.get('school_id')
            school = School.objects.filter(id=school_id, tenant=tenant).first() if school_id else School.objects.filter(tenant=tenant).first()
            
            if name and code and school:
                from backend.apps.academic.models import SubjectCategory
                code = code.strip().lower().replace(' ', '-')
                SubjectCategory.objects.get_or_create(
                    tenant=tenant,
                    school=school,
                    code=code,
                    defaults={'name': name}
                )
        elif action == 'delete':
            subject_id = request.POST.get('subject_id')
            if subject_id:
                from backend.apps.academic.models import Subject
                Subject.objects.filter(id=subject_id, tenant=tenant).delete()
                
        return redirect('subject_management_web')


class GradebookWebView(RoleRequiredMixin, View):
    """
    Enterprise Class Matrix Gradebook View for Teachers & School Admins.
    """
    required_roles = [ROLE_SCHOOL_ADMIN, ROLE_TEACHER]

    def get(self, request):
        tenant = getattr(request, 'tenant', None)
        classes = AcademicClass.objects.filter(tenant=tenant)
        subjects = Subject.objects.filter(tenant=tenant)
        years = AcademicYear.objects.filter(tenant=tenant)
        
        selected_class_id = request.GET.get('class_id') or (classes.first().id if classes.exists() else None)
        selected_subject_id = request.GET.get('subject_id') or (subjects.first().id if subjects.exists() else None)
        selected_year_id = request.GET.get('year_id') or (years.first().id if years.exists() else None)
        
        selected_class = AcademicClass.objects.filter(id=selected_class_id).first() if selected_class_id else None
        selected_subject = Subject.objects.filter(id=selected_subject_id).first() if selected_subject_id else None
        selected_year = AcademicYear.objects.filter(id=selected_year_id).first() if selected_year_id else None
        
        periods = selected_year.periods.all() if selected_year else []
        selected_period_id = request.GET.get('period_id') or (periods.first().id if periods.exists() else None)
        selected_period = selected_year.periods.filter(id=selected_period_id).first() if selected_year and selected_period_id else None

        entries = []
        if selected_class and selected_subject and selected_year:
            from backend.apps.academic.services import GradebookService
            entries = GradebookService.get_or_create_grid(
                academic_class=selected_class,
                subject=selected_subject,
                period=selected_period,
                academic_year=selected_year,
                tenant=tenant
            )

        context = {
            'classes': classes,
            'subjects': subjects,
            'years': years,
            'periods': periods,
            'selected_class': selected_class,
            'selected_subject': selected_subject,
            'selected_year': selected_year,
            'selected_period': selected_period,
            'entries': entries
        }
        return render(request, 'academic/gradebook.html', context)

    def post(self, request):
        entry_id = request.POST.get('entry_id')
        ca_score = request.POST.get('ca_score', 0)
        exam_score = request.POST.get('exam_score', 0)
        is_absent = request.POST.get('is_absent') == 'true'
        teacher_notes = request.POST.get('teacher_notes', '')

        if entry_id:
            from backend.apps.academic.services import GradebookService
            try:
                entry = GradebookService.save_scores(
                    entry_id=entry_id,
                    ca_score=ca_score,
                    exam_score=exam_score,
                    is_absent=is_absent,
                    teacher_notes=teacher_notes,
                    user=request.user
                )
                if request.headers.get('HX-Request'):
                    return HttpResponse(f"""
                        <tr id="entry-row-{entry.id}" class="hover:bg-slate-800/30 transition duration-150">
                            <td class="px-6 py-4 font-semibold text-white">{entry.student.person.get_full_name()}</td>
                            <td class="px-6 py-4"><input type="number" step="0.1" name="ca_score" value="{entry.ca_score}" class="w-20 px-2 py-1 bg-slate-900 border border-slate-700 rounded text-white text-center"></td>
                            <td class="px-6 py-4"><input type="number" step="0.1" name="exam_score" value="{entry.exam_score}" class="w-20 px-2 py-1 bg-slate-900 border border-slate-700 rounded text-white text-center"></td>
                            <td class="px-6 py-4 text-center font-bold text-emerald-400">{entry.total_score}</td>
                            <td class="px-6 py-4 text-center"><span class="px-2 py-1 bg-indigo-500/20 text-indigo-300 rounded font-mono font-bold text-xs">{entry.letter_grade}</span></td>
                            <td class="px-6 py-4 text-xs text-slate-400">{entry.remark}</td>
                        </tr>
                    """)
            except Exception as e:
                return HttpResponse(f'<span class="text-rose-400 text-xs">{str(e)}</span>')

        return redirect('gradebook_web')


class ReportCardWebView(View):
    """
    Official Student Report Card View supporting PDF/Print rendering & QR validation.
    """
    def get(self, request):
        tenant = getattr(request, 'tenant', None)
        qr_code = request.GET.get('verify')
        
        if qr_code:
            from backend.apps.academic.services import ReportCardService
            report = ReportCardService.verify_qr_code(qr_code)
            return render(request, 'academic/report_card_verification.html', {'report': report})

        from backend.apps.people.models import StudentProfile
        student_id = request.GET.get('student_id')
        student = StudentProfile.objects.filter(id=student_id).first() if student_id else StudentProfile.objects.filter(tenant=tenant).first()

        if not student:
            return redirect('academic_dashboard_web')

        years = AcademicYear.objects.filter(tenant=tenant)
        selected_year = years.first()
        selected_period = selected_year.periods.first() if selected_year else None

        from backend.apps.academic.services import ReportCardService
        report = ReportCardService.compile_student_report_card(
            student=student,
            period=selected_period,
            academic_year=selected_year
        )

        entries = GradebookEntry.objects.filter(
            student=student,
            academic_class=student.academic_class,
            academic_year=selected_year,
            period=selected_period
        )

        context = {
            'student': student,
            'report': report,
            'entries': entries,
            'selected_year': selected_year,
            'selected_period': selected_period
        }
        return render(request, 'academic/report_card.html', context)

    def post(self, request):
        report_id = request.POST.get('report_id')
        teacher_comments = request.POST.get('teacher_comments')
        principal_comments = request.POST.get('principal_comments')
        
        if report_id:
            from backend.apps.academic.models import StudentReportCard
            report = StudentReportCard.objects.filter(id=report_id).first()
            if report:
                if teacher_comments:
                    report.teacher_comments = teacher_comments
                if principal_comments:
                    report.principal_comments = principal_comments
                report.save()
                
        return redirect('report_card_web')


class PromotionWebView(RoleRequiredMixin, View):
    """
    Batch Student Promotion Workspace.
    """
    required_roles = [ROLE_SCHOOL_ADMIN]

    def get(self, request):
        tenant = getattr(request, 'tenant', None)
        classes = AcademicClass.objects.filter(tenant=tenant)
        years = AcademicYear.objects.filter(tenant=tenant)
        
        from_class_id = request.GET.get('from_class_id')
        to_class_id = request.GET.get('to_class_id')
        year_id = request.GET.get('year_id')
        
        from_class = AcademicClass.objects.filter(id=from_class_id).first() if from_class_id else classes.first()
        to_class = AcademicClass.objects.filter(id=to_class_id).first() if to_class_id else (classes[1] if classes.count() > 1 else None)
        selected_year = AcademicYear.objects.filter(id=year_id).first() if year_id else years.first()

        preview = None
        if from_class and selected_year:
            from backend.apps.academic.services import PromotionService
            preview = PromotionService.preview_promotion(from_class, selected_year)

        context = {
            'classes': classes,
            'years': years,
            'from_class': from_class,
            'to_class': to_class,
            'selected_year': selected_year,
            'preview': preview
        }
        return render(request, 'academic/promotions.html', context)

    def post(self, request):
        from_class_id = request.POST.get('from_class_id')
        to_class_id = request.POST.get('to_class_id')
        year_id = request.POST.get('year_id')
        student_ids = request.POST.getlist('student_ids')

        if from_class_id and to_class_id and year_id and student_ids:
            from_class = AcademicClass.objects.get(id=from_class_id)
            to_class = AcademicClass.objects.get(id=to_class_id)
            selected_year = AcademicYear.objects.get(id=year_id)
            
            from backend.apps.academic.services import PromotionService
            PromotionService.execute_batch_promotion(
                from_class=from_class,
                to_class=to_class,
                student_ids=student_ids,
                academic_year=selected_year,
                executed_by_user=request.user
            )

        return redirect('promotion_web')

