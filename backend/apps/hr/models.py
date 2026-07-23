import uuid
from django.db import models
from django.utils import timezone
from backend.apps.core.models import TenantBaseModel, PlatformBaseModel

# ==============================================================
# EMPLOYEE DIRECTORIES & PROFILES
# ==============================================================

class EmployeeProfile(TenantBaseModel):
    """
    Extends the PMC base Person model with HR-specific parameters (pay scales, codes).
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('probation', 'Probation'),
        ('suspended', 'Suspended'),
        ('exited', 'Exited')
    ]
    person = models.OneToOneField('people.Person', on_delete=models.CASCADE, related_name='employee_profile')
    employee_number = models.CharField(max_length=100, unique=True)
    job_title = models.CharField(max_length=150)
    salary_grade = models.CharField(max_length=50, default='grade_1')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='active')
    joined_date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"{self.employee_number}: {self.person.first_name} {self.person.last_name}"


# ==============================================================
# APPLICANT TRACKING & RECRUITMENT
# ==============================================================

class JobOpening(TenantBaseModel):
    title = models.CharField(max_length=150)
    description = models.TextField()
    department = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.title


class Candidate(TenantBaseModel):
    STATUS_CHOICES = [
        ('applied', 'Applied'),
        ('interviewing', 'Interviewing'),
        ('offered', 'Offered'),
        ('hired', 'Hired'),
        ('rejected', 'Rejected')
    ]
    job_opening = models.ForeignKey(JobOpening, on_delete=models.CASCADE, related_name='candidates')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='applied')

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.status})"

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        old_status = None
        if not is_new:
            try:
                old_status = Candidate.objects.get(pk=self.pk).status
            except Exception:
                pass
        
        super().save(*args, **kwargs)
        
        if self.status == 'hired' and (is_new or old_status != 'hired'):
            self.convert_to_employee()

    def convert_to_employee(self, department_name=None, salary_grade=None, job_title=None, school=None):
        from datetime import timedelta
        from backend.apps.people.models import Person, StaffProfile, PersonRole
        from backend.apps.identity.models import User, Role, TenantMembership
        from backend.apps.hr.models import EmployeeProfile, OnboardingTask, LeaveBalance, OrgAssignmentHistory
        from backend.apps.core.events import event_bus, DomainEvent
        
        # 1. Check if Employee already exists
        emp_exists = EmployeeProfile.objects.filter(tenant=self.tenant, person__user__email=self.email).exists()
        if emp_exists:
            return
            
        # 2. Find or Create Person record
        person = Person.objects.filter(tenant=self.tenant, user__email=self.email).first()
        if not person:
            person = Person.objects.create(
                tenant=self.tenant,
                person_number=f"PER-{uuid.uuid4().hex[:6].upper()}",
                first_name=self.first_name,
                last_name=self.last_name,
                gender='other',
                date_of_birth=timezone.now().date()
            )
            
        # 3. Create Django User
        if not person.user:
            username = f"{self.first_name.lower()}.{self.last_name.lower()}"
            counter = 1
            base_username = username
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
                
            user = User.objects.create_user(
                username=username,
                email=self.email,
                password="ChangeMe123!"
            )
            person.user = user
            person.save()
        else:
            user = person.user
        
        # 4. Map Tenant Membership Role
        r_code = f"staff_{self.tenant.id.hex[:8]}"
        role_obj = Role.objects.filter(code=r_code, tenant=self.tenant).first()
        if not role_obj:
            role_obj = Role.objects.create(
                tenant=self.tenant,
                code=r_code,
                name="Staff"
            )
        TenantMembership.objects.get_or_create(
            user=user,
            tenant=self.tenant,
            role=role_obj
        )
        
        # 5. Add PersonRole entry
        from backend.apps.tenants.models import School
        school_obj = school or School.objects.filter(tenant=self.tenant).first()
        PersonRole.objects.get_or_create(
            tenant=self.tenant,
            person=person,
            role='staff',
            school=school_obj
        )
        
        # 6. Create profiles
        emp_num = f"EMP-{uuid.uuid4().hex[:6].upper()}"
        employee = EmployeeProfile.objects.create(
            tenant=self.tenant,
            person=person,
            employee_number=emp_num,
            job_title=job_title or 'Support Staff',
            salary_grade=salary_grade or 'grade_1',
            status='active'
        )
        
        StaffProfile.objects.create(
            tenant=self.tenant,
            person=person,
            employee_number=emp_num,
            role_type='Support'
        )
        
        # 7. Seed Onboarding checklist tasks
        tasks = [
            ('Submit signed employment contract', 'contract'),
            ('Identity verification and capturing', 'identity'),
            ('Background reference check', 'background'),
            ('Medical clearance report submission', 'medical'),
            ('Compliance and safety policy signoff', 'policy')
        ]
        for t_name, cat in tasks:
            OnboardingTask.objects.get_or_create(
                tenant=self.tenant,
                employee=employee,
                task_name=t_name,
                category=cat,
                defaults={'due_date': timezone.now().date() + timedelta(days=7)}
            )
            
        # 8. Seed Leave balance
        LeaveBalance.objects.get_or_create(
            tenant=self.tenant,
            employee=employee,
            leave_type='annual',
            defaults={'allowed_days': 20, 'remaining_days': 20}
        )
        
        # 9. Seed Org history
        OrgAssignmentHistory.objects.get_or_create(
            tenant=self.tenant,
            employee=employee,
            defaults={
                'campus_name': school_obj.name if school_obj else 'Grace Main Campus',
                'department_name': department_name or 'Administration',
                'job_position': job_title or 'Support Staff',
                'is_active': True
            }
        )
        
        # 10. Publish Domain Event
        event_bus.publish(DomainEvent("employee.onboarded", tenant_id=str(self.tenant.id), data={"id": str(employee.id)}))



class Interview(TenantBaseModel):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='interviews')
    interview_date = models.DateTimeField(default=timezone.now)
    score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Interview for {self.candidate.first_name} on {self.interview_date}"


# ==============================================================
# LEAVE MANAGEMENT CALENDARS
# ==============================================================

class LeaveRequest(TenantBaseModel):
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ]
    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.CharField(max_length=50)  # annual, sick, maternity
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    reason = models.TextField(blank=True)

    def __str__(self):
        return f"{self.employee.employee_number}: {self.leave_type} ({self.status})"


class LeaveBalance(TenantBaseModel):
    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='leave_balances')
    leave_type = models.CharField(max_length=50)
    allowed_days = models.IntegerField(default=20)
    remaining_days = models.IntegerField(default=20)

    def __str__(self):
        return f"{self.employee.employee_number}: {self.leave_type} ({self.remaining_days}/{self.allowed_days})"


# ==============================================================
# PAYROLL CALCULATIONS ENGINE
# ==============================================================

class PayrollPeriod(TenantBaseModel):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('paid', 'Paid')
    ]
    name = models.CharField(max_length=100)  # e.g., July 2026 Payroll
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='draft')

    def __str__(self):
        return self.name


class SalaryStructure(TenantBaseModel):
    grade = models.CharField(max_length=50, unique=True)
    base_salary = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.grade}: {self.base_salary}"


class PayrollRun(TenantBaseModel):
    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='payroll_runs')
    period = models.ForeignKey(PayrollPeriod, on_delete=models.CASCADE)
    earnings = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    net_pay = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=30, default='draft')  # draft, approved, paid

    def __str__(self):
        return f"{self.employee.employee_number} net pay: {self.net_pay} ({self.status})"


# ==============================================================
# PERFORMANCE APPRAISALS & PROFESSIONAL DEVELOPMENT
# ==============================================================

class PerformanceReview(TenantBaseModel):
    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='appraisals')
    reviewer = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='appraisals_conducted')
    score = models.DecimalField(max_digits=5, decimal_places=2)
    review_date = models.DateField(default=timezone.now)
    remarks = models.TextField(blank=True)

    def __str__(self):
        return f"Review: {self.employee.employee_number} Score: {self.score}"


class TrainingProgram(TenantBaseModel):
    name = models.CharField(max_length=150)
    cost = models.DecimalField(max_digits=12, decimal_places=2)
    cpd_hours = models.IntegerField(default=0)

    def __str__(self):
        return self.name


# ==============================================================
# ONBOARDING & TRANSITION CHECKLISTS
# ==============================================================

class OnboardingChecklist(TenantBaseModel):
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class OnboardingTask(TenantBaseModel):
    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='onboarding_tasks')
    task_name = models.CharField(max_length=150)
    category = models.CharField(max_length=50, default='General') # contract, identity, medical, background, policy, accounts
    due_date = models.DateField()
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks_verified')

    def __str__(self):
        return f"{self.task_name} - {self.employee.employee_number} ({'Done' if self.is_completed else 'Pending'})"


# ==============================================================
# COMPANY ASSETS ALLOCATIONS (INVENTORY INTEGRATIONS)
# ==============================================================

class EmployeeAsset(TenantBaseModel):
    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='assigned_assets')
    asset_name = models.CharField(max_length=150)
    serial_number = models.CharField(max_length=100, blank=True)
    asset_type = models.CharField(max_length=50, default='IT Equipment') # Laptop, Desktop, Phone, Key Card, Vehicle
    date_assigned = models.DateField(default=timezone.now)
    date_returned = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.asset_name} ({self.serial_number}) - {self.employee.employee_number}"


# ==============================================================
# ORGANIZATIONAL STRUCTURE & CONFIGS HISTORY
# ==============================================================

class OrgAssignmentHistory(TenantBaseModel):
    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='assignment_history')
    campus_name = models.CharField(max_length=150, blank=True)
    department_name = models.CharField(max_length=150, blank=True)
    cost_centre = models.CharField(max_length=100, blank=True)
    job_position = models.CharField(max_length=150, blank=True)
    manager = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='subordinates_history')
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.job_position} - {self.employee.employee_number}"


# ==============================================================
# PERFORMANCE OBJECTIVES & TARGETS
# ==============================================================

class PerformanceObjective(TenantBaseModel):
    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='objectives')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    target_date = models.DateField()
    progress_percentage = models.IntegerField(default=0)
    status = models.CharField(max_length=30, default='not_started') # not_started, in_progress, achieved, cancelled

    def __str__(self):
        return f"{self.title} ({self.progress_percentage}%) - {self.employee.employee_number}"

