from django.shortcuts import render, redirect
from django.views import View
from django.http import HttpResponse
from django.utils import timezone
from datetime import timedelta
from backend.apps.tenants.models import School
from backend.apps.academic.models import AcademicYear, EducationLevel, AcademicClass, Subject

class AcademicWizardWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
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


class AcademicDashboardWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        schools = School.objects.filter(tenant=getattr(request, 'tenant', None))
        # Choose first school defaults context
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


class SubjectManagementWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
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
