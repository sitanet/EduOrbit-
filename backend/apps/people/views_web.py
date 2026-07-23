from django.shortcuts import render, redirect
from django.views import View
from django.http import HttpResponse
from django.db.models import Q
from backend.apps.people.models import Person, FamilyRelationship

class PersonDirectoryWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        tenant = getattr(request, 'tenant', None)
        from backend.apps.tenants.models import School
        active_school_id = request.session.get('active_school_id')
        active_school = School.objects.filter(id=active_school_id, tenant=tenant).first() if active_school_id else None
        if not active_school:
            active_school = School.objects.filter(tenant=tenant).first()
            
        query = request.GET.get('q', '')
        if query:
            people = Person.objects.filter(
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(person_number__icontains=query),
                tenant=tenant,
                assigned_roles__school=active_school
            ).distinct()
        else:
            people = Person.objects.filter(tenant=tenant, assigned_roles__school=active_school).distinct()
            
        context = {
            'people': people,
            'query': query
        }
        return render(request, 'people/directory.html', context)

    def post(self, request):
        if not request.user.is_authenticated:
            return HttpResponse("Unauthorized", status=401)
            
        tenant = getattr(request, 'tenant', None)
        action = request.POST.get('action') or request.GET.get('action')
        
        if action == 'edit':
            person_id = request.POST.get('person_id') or request.GET.get('person_id')
            try:
                person = Person.objects.get(id=person_id, tenant=tenant)
                person.first_name = request.POST.get('first_name')
                person.last_name = request.POST.get('last_name')
                person.middle_name = request.POST.get('middle_name', '')
                person.gender = request.POST.get('gender')
                person.date_of_birth = request.POST.get('date_of_birth')
                person.save()
                return HttpResponse(
                    '<div class="p-3 text-xs text-emerald-800 rounded-lg bg-emerald-50 dark:bg-slate-900 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-900/30" role="alert">'
                    '<span class="font-semibold">Success:</span> Person profile updated successfully!'
                    '</div>'
                    '<script>setTimeout(() => { window.location.reload(); }, 1000);</script>'
                )
            except Exception as e:
                return HttpResponse(
                    f'<div class="p-3 text-xs text-red-800 rounded-lg bg-red-50 dark:bg-slate-900 dark:text-red-400 border border-red-200 dark:border-red-900/30" role="alert">'
                    f'<span class="font-semibold">Error:</span> {str(e)}'
                    f'</div>'
                )
                
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        middle_name = request.POST.get('middle_name', '')
        gender = request.POST.get('gender')
        date_of_birth = request.POST.get('date_of_birth')
        role_type = request.POST.get('role_type') # 'student', 'teacher', 'parent', 'none'
        
        import uuid
        person_number = request.POST.get('person_number')
        if not person_number:
            person_number = f"PER-{uuid.uuid4().hex[:6].upper()}"
            
        try:
            person = Person.objects.create(
                tenant=tenant,
                person_number=person_number,
                first_name=first_name,
                last_name=last_name,
                middle_name=middle_name,
                gender=gender,
                date_of_birth=date_of_birth
            )
            
            from backend.apps.tenants.models import School
            from backend.apps.people.models import PersonRole, StudentProfile, TeacherProfile, ParentProfile
            from backend.apps.identity.models import User, TenantMembership, Role
            
            active_school_id = request.session.get('active_school_id')
            school = School.objects.filter(id=active_school_id, tenant=tenant).first() if active_school_id else None
            if not school:
                school = School.objects.filter(tenant=tenant).first()
                
            username = f"{first_name.lower()}.{last_name.lower()}".replace(" ", "")
            
            # Ensure unique username
            counter = 1
            base_username = username
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
                
            email = f"{username}@eduorbit.com"
            default_password = "ChangeMe123!"
            
            # 1. Create Django User
            user = User.objects.create_user(
                username=username,
                email=email,
                password=default_password
            )
            person.user = user
            person.save()
            
            if role_type in ['student', 'teacher', 'parent', 'none'] and school:
                role_val = 'staff' if role_type == 'none' else role_type
                # 2. Add PersonRole entry
                PersonRole.objects.create(
                    tenant=tenant,
                    person=person,
                    role=role_val,
                    school=school
                )
                
                # 3. Add specific profiles
                if role_type == 'student':
                    StudentProfile.objects.create(
                        tenant=tenant,
                        person=person,
                        student_number=f"STU-{uuid.uuid4().hex[:6].upper()}",
                        current_school=school
                    )
                elif role_type == 'teacher':
                    emp_num = f"EMP-{uuid.uuid4().hex[:6].upper()}"
                    TeacherProfile.objects.create(
                        tenant=tenant,
                        person=person,
                        employee_number=emp_num
                    )
                    try:
                        from backend.apps.hr.models import EmployeeProfile
                        EmployeeProfile.objects.create(
                            tenant=tenant,
                            person=person,
                            employee_number=emp_num,
                            job_title='Teacher',
                            status='active'
                        )
                    except Exception:
                        pass
                elif role_type == 'parent':
                    ParentProfile.objects.create(
                        tenant=tenant,
                        person=person,
                        parent_number=f"PAR-{uuid.uuid4().hex[:6].upper()}"
                    )
                elif role_type == 'none':
                    emp_num = f"EMP-{uuid.uuid4().hex[:6].upper()}"
                    from backend.apps.people.models import StaffProfile
                    StaffProfile.objects.create(
                        tenant=tenant,
                        person=person,
                        employee_number=emp_num,
                        role_type='Support'
                    )
                    try:
                        from backend.apps.hr.models import EmployeeProfile
                        EmployeeProfile.objects.create(
                            tenant=tenant,
                            person=person,
                            employee_number=emp_num,
                            job_title='Support Staff',
                            status='active'
                        )
                    except Exception:
                        pass
                    
                # 4. Map Tenant Membership Role
                r_code = f"{role_val}_{tenant.id.hex[:8]}"
                role_obj = Role.objects.filter(code=r_code, tenant=tenant).first()
                if not role_obj:
                    role_obj = Role.objects.create(
                        tenant=tenant,
                        code=r_code,
                        name=role_val.title()
                    )
                TenantMembership.objects.create(
                    user=user,
                    tenant=tenant,
                    role=role_obj
                )
        except Exception as e:
            return HttpResponse(
                f'<div class="p-3 text-xs text-red-800 rounded-lg bg-red-50 dark:bg-slate-900 dark:text-red-400 border border-red-200 dark:border-red-900/30" role="alert">'
                f'<span class="font-semibold">Error:</span> {str(e)}'
                f'</div>'
            )
            
        return HttpResponse(
            f'<div class="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 space-y-2 text-xs">'
            f'  <p class="font-bold text-white">🎉 Person Profile &amp; User Account Created!</p>'
            f'  <p class="text-slate-350">Deliver the following credentials to the user to log in:</p>'
            f'  <div class="bg-slate-900/60 p-2.5 rounded-lg font-mono space-y-1 text-[11px] text-slate-200 border border-slate-800">'
            f'    <div><strong>Username:</strong> {username}</div>'
            f'    <div><strong>Password:</strong> {default_password}</div>'
            f'    <div><strong>Email:</strong> {email}</div>'
            f'  </div>'
            f'</div>'
        )

    def delete(self, request):
        if not request.user.is_authenticated:
            return HttpResponse("Unauthorized", status=401)
        person_id = request.GET.get('person_id')
        if person_id:
            try:
                person = Person.objects.get(id=person_id, tenant=getattr(request, 'tenant', None))
                if person.user:
                    person.user.delete()
                person.delete()
                return HttpResponse("")
            except Exception as e:
                return HttpResponse(f"Error: {str(e)}", status=400)
        return HttpResponse("Missing ID", status=400)


class FamilyRelationshipWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        relationships = FamilyRelationship.objects.filter(tenant=getattr(request, 'tenant', None)).select_related('student', 'relative')
        return render(request, 'people/relationship_manager.html', {'relationships': relationships})
