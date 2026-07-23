from django.shortcuts import render, redirect
from django.views import View
from django.http import HttpResponse
from backend.apps.tenants.models import School
from backend.apps.admissions.models import AdmissionCampaign, AdmissionApplication

class AdmissionsWizardWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        schools = School.objects.filter(tenant=getattr(request, 'tenant', None))
        return render(request, 'admissions/setup_wizard.html', {'schools': schools})

    def post(self, request):
        # Stepper wizard application loader
        school_id = request.POST.get('school_id')
        campaign_name = request.POST.get('campaign_name')
        
        try:
            school = School.objects.get(id=school_id, tenant=getattr(request, 'tenant', None))
            # Fetch default active academic year
            from backend.apps.academic.models import AcademicYear
            active_year = AcademicYear.objects.filter(school=school, status='active').first()
            if not active_year:
                raise ValueError("Active academic year not found. Complete Academic setup first.")
                
            # Create campaign
            import datetime
            campaign = AdmissionCampaign.objects.create(
                school=school,
                tenant=getattr(request, 'tenant', None),
                academic_year=active_year,
                name=campaign_name,
                start_date=datetime.date.today(),
                end_date=datetime.date.today() + datetime.timedelta(days=120)
            )
        except Exception as e:
            return HttpResponse(
                f'<div class="p-4 mb-4 text-sm text-red-800 rounded-xl bg-red-50 dark:bg-slate-900 dark:text-red-400 border border-red-200 dark:border-red-900/30" role="alert">'
                f'<span class="font-semibold">Failed initializing admissions:</span> {str(e)}'
                f'</div>'
            )

        return HttpResponse(
            '<div class="p-4 mb-4 text-sm text-emerald-800 rounded-xl bg-emerald-50 dark:bg-slate-900 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-900/30" role="alert">'
            '<h3 class="font-bold text-base mb-1">Admissions Setup Complete!</h3>'
            '<p>Redirecting to dashboard...</p>'
            '</div>'
            '<script>setTimeout(() => { window.location.href = "/admissions/dashboard/"; }, 2000);</script>'
        )


class AdmissionsDashboardWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        schools = School.objects.filter(tenant=getattr(request, 'tenant', None))
        active_school = schools.first()
        
        campaigns = AdmissionCampaign.objects.filter(school=active_school) if active_school else []
        applications = AdmissionApplication.objects.filter(intake__campaign__school=active_school) if active_school else []
        
        context = {
            'schools': schools,
            'active_school': active_school,
            'campaigns': campaigns,
            'applications': applications
        }
        return render(request, 'admissions/dashboard.html', context)


from backend.apps.academic.models import AcademicLevel, AcademicYear
from backend.apps.admissions.models import AdmissionCampaign, AdmissionIntake, Applicant, AdmissionApplication, FormSubmission, ApplicationDocument
from backend.apps.people.models import Person, DocumentType

class AdmissionsApplicationCreateWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        tenant = getattr(request, 'tenant', None)
        from backend.apps.tenants.models import School
        active_school_id = request.session.get('active_school_id')
        active_school = School.objects.filter(id=active_school_id, tenant=tenant).first() if active_school_id else None
        if not active_school:
            active_school = School.objects.filter(tenant=tenant).first()
            
        if active_school:
            active_year = AcademicYear.objects.filter(school=active_school, status='active').first()
            if not active_year:
                import datetime
                active_year = AcademicYear.objects.create(
                    school=active_school,
                    tenant=tenant,
                    name="2024/2025",
                    code="2024-2025",
                    start_date=datetime.date(2024, 9, 1),
                    end_date=datetime.date(2025, 7, 30),
                    status='active'
                )
                
            campaign = AdmissionCampaign.objects.filter(school=active_school, is_active=True).first()
            if not campaign:
                import datetime
                campaign = AdmissionCampaign.objects.create(
                    school=active_school,
                    tenant=tenant,
                    academic_year=active_year,
                    name="Main Admissions Campaign",
                    start_date=datetime.date.today(),
                    end_date=datetime.date.today() + datetime.timedelta(days=120)
                )
                
            intake = AdmissionIntake.objects.filter(campaign=campaign).first()
            if not intake:
                intake = AdmissionIntake.objects.create(
                    campaign=campaign,
                    tenant=tenant,
                    name="First Batch Intake",
                    status="open"
                )
                
        intakes = AdmissionIntake.objects.filter(campaign__school=active_school)
        levels = AcademicLevel.objects.filter(education_level__school=active_school)
        
        if not levels.exists() and active_school:
            from backend.apps.academic.models import EducationLevel
            edu_level, _ = EducationLevel.objects.get_or_create(
                school=active_school,
                tenant=tenant,
                name="Secondary",
                code="secondary"
            )
            levels = [
                AcademicLevel.objects.create(education_level=edu_level, tenant=tenant, name="JSS 1", code="jss-1"),
                AcademicLevel.objects.create(education_level=edu_level, tenant=tenant, name="SSS 1", code="sss-1")
            ]
            
        context = {
            'intakes': intakes,
            'levels': levels,
            'active_school': active_school
        }
        return render(request, 'admissions/new_application.html', context)
        
    def post(self, request):
        if not request.user.is_authenticated:
            return HttpResponse("Unauthorized", status=401)
            
        tenant = getattr(request, 'tenant', None)
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        middle_name = request.POST.get('middle_name', '')
        gender = request.POST.get('gender')
        date_of_birth = request.POST.get('date_of_birth')
        target_level_id = request.POST.get('target_level')
        intake_id = request.POST.get('intake')
        
        nationality = request.POST.get('nationality', 'Nigerian')
        state_of_origin = request.POST.get('state_of_origin', '')
        religion = request.POST.get('religion', '')
        
        parent_name = request.POST.get('parent_name')
        parent_phone = request.POST.get('parent_phone')
        parent_email = request.POST.get('parent_email')
        
        prev_school = request.POST.get('prev_school', '')
        prev_gpa = request.POST.get('prev_gpa', '')
        medical_allergies = request.POST.get('medical_allergies', '')
        
        import uuid
        import os
        from django.core.files.storage import default_storage
        from django.core.files.base import ContentFile
        
        try:
            person = Person.objects.create(
                tenant=tenant,
                person_number=f"PER-{uuid.uuid4().hex[:6].upper()}",
                first_name=first_name,
                last_name=last_name,
                middle_name=middle_name,
                gender=gender,
                date_of_birth=date_of_birth,
                nationality=nationality,
                state_of_origin=state_of_origin,
                religion=religion
            )
            
            from backend.apps.tenants.models import School
            active_school_id = request.session.get('active_school_id')
            active_school = School.objects.filter(id=active_school_id, tenant=tenant).first() if active_school_id else None
            if not active_school:
                active_school = School.objects.filter(tenant=tenant).first()
                
            applicant = Applicant.objects.create(
                school=active_school,
                tenant=tenant,
                person=person,
                applicant_number=f"APP-{uuid.uuid4().hex[:6].upper()}"
            )
            
            from backend.apps.admissions.models import FormDefinition
            form_def, _ = FormDefinition.objects.get_or_create(
                school=active_school,
                tenant=tenant,
                name="Admissions General Form",
                code="admissions-general"
            )
            submission = FormSubmission.objects.create(
                form=form_def,
                tenant=tenant,
                submitted_data={
                    "parent_name": parent_name,
                    "parent_phone": parent_phone,
                    "parent_email": parent_email,
                    "prev_school": prev_school,
                    "prev_gpa": prev_gpa,
                    "medical_allergies": medical_allergies
                }
            )
            
            intake = AdmissionIntake.objects.get(id=intake_id)
            target_level = AcademicLevel.objects.get(id=target_level_id)
            
            application = AdmissionApplication.objects.create(
                tenant=tenant,
                intake=intake,
                applicant=applicant,
                target_level=target_level,
                submission=submission,
                status="submitted"
            )
            
            # File uploads handling helper
            def save_document(file_obj, doc_code, doc_name):
                if not file_obj:
                    return
                ext = os.path.splitext(file_obj.name)[1]
                filename = f"admissions/{doc_code}_{uuid.uuid4().hex[:8]}{ext}"
                saved_path = default_storage.save(filename, ContentFile(file_obj.read()))
                
                doc_type, _ = DocumentType.objects.get_or_create(code=doc_code, defaults={'name': doc_name})
                ApplicationDocument.objects.create(
                    tenant=tenant,
                    application=application,
                    document_type=doc_type,
                    document_file=saved_path,
                    verification_status='pending'
                )
                
            save_document(request.FILES.get('birth_certificate'), 'birth_certificate', 'Birth Certificate')
            save_document(request.FILES.get('academic_transcript'), 'academic_transcript', 'Academic Transcript')
            save_document(request.FILES.get('passport_photo'), 'passport_photo', 'Passport Photograph')
            save_document(request.FILES.get('additional_document'), 'additional_document', 'Additional Document')
            
        except Exception as e:
            return HttpResponse(
                f'<div class="p-3 text-xs text-red-800 rounded-lg bg-red-50 dark:bg-slate-900 dark:text-red-400 border border-red-200 dark:border-red-900/30" role="alert">'
                f'<span class="font-semibold">Error:</span> {str(e)}'
                f'</div>'
            )
            
        return HttpResponse(
            '<div class="p-3 text-xs text-emerald-800 rounded-lg bg-emerald-50 dark:bg-slate-900 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-900/30" role="alert">'
            '<span class="font-semibold">Success:</span> Student application submitted successfully!'
            '</div>'
            '<script>setTimeout(() => { window.location.href = "/admissions/dashboard/"; }, 1500);</script>'
        )


class AdmissionsApplicationReviewWebView(View):
    def get(self, request, application_id):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        tenant = getattr(request, 'tenant', None)
        application = AdmissionApplication.objects.filter(
            id=application_id, 
            intake__campaign__tenant=tenant
        ).select_related('applicant__person', 'intake__campaign', 'target_level', 'submission').first()
        
        if not application:
            return HttpResponse("Application not found", status=404)
            
        documents = application.documents.all()
        submitted_data = application.submission.submitted_data if application.submission else {}
        
        context = {
            'application': application,
            'documents': documents,
            'submitted_data': submitted_data
        }
        return render(request, 'admissions/review.html', context)
        
    def post(self, request, application_id):
        if not request.user.is_authenticated:
            return HttpResponse("Unauthorized", status=401)
            
        tenant = getattr(request, 'tenant', None)
        application = AdmissionApplication.objects.filter(
            id=application_id, 
            intake__campaign__tenant=tenant
        ).first()
        
        if not application:
            return HttpResponse("Application not found", status=404)
            
        action = request.POST.get('action')
        if action == 'accept':
            application.status = 'accepted'
            application.save()
            
            # Auto-enroll student profile
            person = application.applicant.person
            from backend.apps.people.models import PersonRole, StudentProfile
            from backend.apps.identity.models import Role
            role_code = f"student_{tenant.id if tenant else 'default'}"
            role, _ = Role.objects.get_or_create(code=role_code, defaults={'name': 'Student'})
            PersonRole.objects.get_or_create(person=person, role=role)
            
            import uuid
            StudentProfile.objects.get_or_create(
                person=person,
                defaults={
                    'tenant': tenant,
                    'student_number': f"STU-{uuid.uuid4().hex[:6].upper()}",
                    'current_school': application.applicant.school,
                    'enrollment_status': 'active'
                }
            )
        elif action == 'reject':
            application.status = 'rejected'
            application.save()
        elif action == 'waitlist':
            application.status = 'waitlisted'
            application.save()
            
        return redirect('admissions_dashboard_web')
