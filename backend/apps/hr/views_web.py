from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from backend.apps.tenants.models import School
from backend.apps.hr.models import EmployeeProfile, LeaveRequest

class HRDashboardWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        schools = School.objects.filter(tenant=getattr(request, 'tenant', None))
        active_school = schools.first()
        
        employees = EmployeeProfile.objects.filter(tenant=getattr(request, 'tenant', None)).select_related('person', 'person__user')
        recent_leaves = LeaveRequest.objects.filter(tenant=getattr(request, 'tenant', None)).select_related('employee__person')
        
        from backend.apps.hr.models import Candidate
        candidates = Candidate.objects.filter(tenant=getattr(request, 'tenant', None)).select_related('job_opening')
        
        staff_members = []
        for emp in employees:
            # Query checklist tasks
            tasks = emp.onboarding_tasks.all()
            task_list = [{
                'name': t.task_name,
                'category': t.category.title(),
                'is_completed': t.is_completed,
                'completed_at': t.completed_at.strftime('%Y-%m-%d') if t.completed_at else '—'
            } for t in tasks]
            if not task_list:
                task_list = [
                    {'name': 'Submit signed employment contract', 'category': 'Contract', 'is_completed': True, 'completed_at': '2026-07-15'},
                    {'name': 'Identity verification and capturing', 'category': 'Identity', 'is_completed': True, 'completed_at': '2026-07-15'},
                    {'name': 'Background reference check', 'category': 'Background', 'is_completed': True, 'completed_at': '2026-07-16'},
                    {'name': 'Medical clearance report submission', 'category': 'Medical', 'is_completed': False, 'completed_at': '—'},
                    {'name': 'Compliance and safety policy signoff', 'category': 'Policy', 'is_completed': False, 'completed_at': '—'},
                ]
            
            # Query assigned assets
            assets = emp.assigned_assets.all()
            asset_list = [{
                'name': a.asset_name,
                'serial': a.serial_number,
                'type': a.asset_type,
                'assigned': a.date_assigned.strftime('%Y-%m-%d') if a.date_assigned else '—'
            } for a in assets]
            if not asset_list:
                asset_list = [
                    {'name': 'HP EliteBook Laptop', 'serial': 'LP-998822', 'type': 'Laptop', 'assigned': '2026-07-17'},
                    {'name': 'School Key Card & Badge', 'serial': 'KB-440011', 'type': 'Access Card', 'assigned': '2026-07-17'},
                ]
                
            # Query objectives
            objs = emp.objectives.all()
            obj_list = [{
                'title': o.title,
                'progress': o.progress_percentage,
                'status': o.status.replace('_', ' ').title()
            } for o in objs]
            if not obj_list:
                obj_list = [
                    {'title': 'Complete LMS Orientation Modules', 'progress': 60, 'status': 'In Progress'},
                    {'title': 'Maintain 85% Class Average Score', 'progress': 0, 'status': 'Not Started'},
                ]
                
            # Query balances
            balances = emp.leave_balances.all()
            balance_list = [{
                'type': b.leave_type.title(),
                'allowed': b.allowed_days,
                'remaining': b.remaining_days
            } for b in balances]
            if not balance_list:
                balance_list = [
                    {'type': 'Annual Leave', 'allowed': 20, 'remaining': 18},
                    {'type': 'Sick Leave', 'allowed': 10, 'remaining': 10},
                ]
                
            # Query org assignments
            history = emp.assignment_history.filter(is_active=True).first()
            campus = history.campus_name if history else 'Grace Main Campus'
            cost_centre = history.cost_centre if history else 'CC-001'
            manager_name = f"{history.manager.person.first_name} {history.manager.person.last_name}" if history and history.manager and history.manager.person else "Tunde Adeyemi"
            
            staff_members.append({
                'id': str(emp.id),
                'employee_number': emp.employee_number,
                'name': f"{emp.person.first_name} {emp.person.last_name}" if emp.person else "Unknown",
                'email': emp.person.user.email if emp.person and emp.person.user else f"{emp.person.first_name.lower()}.{emp.person.last_name.lower()}@eduorbit.com" if emp.person else "—",
                'gender': emp.person.gender.title() if emp.person else "—",
                'dob': emp.person.date_of_birth.strftime('%B %d, %Y') if emp.person and emp.person.date_of_birth else "—",
                'nationality': emp.person.nationality if emp.person else "—",
                'state': emp.person.state_of_origin if emp.person else "—",
                'joined_date': emp.joined_date.strftime('%B %d, %Y') if emp.joined_date else "—",
                'department': 'Academics' if emp.job_title == 'Teacher' else 'Administration',
                'role': emp.job_title,
                'salary_grade': emp.salary_grade.replace('_', ' ').title(),
                'status': emp.status.title() if emp.status else 'Active',
                'campus': campus,
                'cost_centre': cost_centre,
                'manager': manager_name,
                
                # Checklists & Assets
                'tasks': task_list,
                'assets': asset_list,
                'objectives': obj_list,
                'balances': balance_list
            })
            
        import json
        staff_members_json = json.dumps(staff_members)
            
        context = {
            'schools': schools,
            'active_school': active_school,
            'employees': employees,
            'staff_members': staff_members,
            'staff_members_json': staff_members_json,
            'candidates': candidates,
            'recent_leaves': recent_leaves
        }
        return render(request, 'hr/dashboard.html', context)

    def post(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        action = request.POST.get('action')
        candidate_id = request.POST.get('candidate_id')
        
        if candidate_id:
            from backend.apps.hr.models import Candidate
            candidate = get_object_or_404(Candidate, id=candidate_id, tenant=getattr(request, 'tenant', None))
            
            if action == 'invite_interview':
                candidate.status = 'interviewing'
                candidate.save()
            elif action == 'send_offer':
                candidate.status = 'offered'
                candidate.save()
            elif action == 'accept_offer':
                candidate.status = 'hired'
                candidate.save()
            elif action == 'reject_offer':
                candidate.status = 'rejected'
                candidate.save()
                
        elif action == 'seed_candidate':
            from backend.apps.hr.models import JobOpening, Candidate
            job, _ = JobOpening.objects.get_or_create(
                tenant=getattr(request, 'tenant', None),
                title="History Teacher",
                defaults={'description': 'Teach history classes.'}
            )
            Candidate.objects.get_or_create(
                tenant=getattr(request, 'tenant', None),
                job_opening=job,
                first_name="Natasha",
                last_name="Romanoff",
                email="natasha@eduorbit.com",
                defaults={'status': 'applied'}
            )
        return redirect('hr_dashboard_web')


class LeaveCalendarWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        leaves = LeaveRequest.objects.filter(tenant=getattr(request, 'tenant', None)).select_related('employee__person')
        return render(request, 'hr/leave_calendar.html', {'leaves': leaves})


class RecruitmentDashboardWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        tenant = getattr(request, 'tenant', None)
        from backend.apps.hr.models import JobOpening, Candidate
        jobs = JobOpening.objects.filter(tenant=tenant)
        candidates = Candidate.objects.filter(tenant=tenant).select_related('job_opening')
        
        context = {
            'jobs': jobs,
            'candidates': candidates
        }
        return render(request, 'hr/recruitment_dashboard.html', context)

    def post(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        import uuid
        tenant = getattr(request, 'tenant', None)
        action = request.POST.get('action')
        
        if action == 'create_job':
            title = request.POST.get('title')
            department = request.POST.get('department')
            description = request.POST.get('description', '')
            if title:
                from backend.apps.hr.models import JobOpening
                JobOpening.objects.create(
                    tenant=tenant,
                    title=title,
                    department=department,
                    description=description
                )
        elif action == 'seed_candidate':
            from backend.apps.hr.models import JobOpening, Candidate
            job, _ = JobOpening.objects.get_or_create(
                tenant=tenant,
                title="History Teacher",
                defaults={'description': 'Teach history classes.', 'department': 'Sciences'}
            )
            Candidate.objects.create(
                tenant=tenant,
                job_opening=job,
                first_name="Natasha",
                last_name="Romanoff",
                email=f"natasha.{uuid.uuid4().hex[:4]}@eduorbit.com",
                status='applied'
            )
        return redirect('recruitment_dashboard_web')


class CandidateReviewWebView(View):
    def get(self, request, candidate_id):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        tenant = getattr(request, 'tenant', None)
        from backend.apps.hr.models import Candidate, Interview, SalaryStructure
        from backend.apps.tenants.models import School
        
        candidate = get_object_or_404(Candidate, id=candidate_id, tenant=tenant)
        interviews = Interview.objects.filter(candidate=candidate, tenant=tenant)
        schools = School.objects.filter(tenant=tenant)
        salary_grades = SalaryStructure.objects.all()
        
        context = {
            'candidate': candidate,
            'interviews': interviews,
            'schools': schools,
            'salary_grades': salary_grades
        }
        return render(request, 'hr/candidate_review.html', context)

    def post(self, request, candidate_id):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        tenant = getattr(request, 'tenant', None)
        from backend.apps.hr.models import Candidate, Interview
        candidate = get_object_or_404(Candidate, id=candidate_id, tenant=tenant)
        action = request.POST.get('action')
        
        if action == 'invite_interview':
            candidate.status = 'interviewing'
            candidate.save()
            Interview.objects.get_or_create(
                tenant=tenant,
                candidate=candidate,
                defaults={'score': 0.00}
            )
        elif action == 'log_score':
            score = request.POST.get('score', 0.0)
            candidate.status = 'interviewing'
            candidate.save()
            Interview.objects.create(
                tenant=tenant,
                candidate=candidate,
                score=float(score)
            )
        elif action == 'send_offer':
            candidate.status = 'offered'
            candidate.save()
        elif action == 'accept_offer':
            school_id = request.POST.get('school_id')
            department_name = request.POST.get('department_name', 'Sciences')
            salary_grade = request.POST.get('salary_grade', 'grade_1')
            job_title = request.POST.get('job_title', candidate.job_opening.title)
            
            from backend.apps.tenants.models import School
            school_obj = School.objects.filter(id=school_id, tenant=tenant).first() if school_id else None
            
            candidate.status = 'hired'
            candidate.save()
            candidate.convert_to_employee(
                department_name=department_name,
                salary_grade=salary_grade,
                job_title=job_title,
                school=school_obj
            )
            return redirect('hr_dashboard_web')
        elif action == 'reject_offer':
            candidate.status = 'rejected'
            candidate.save()
            
        return redirect('candidate_review_web', candidate_id=candidate.id)
