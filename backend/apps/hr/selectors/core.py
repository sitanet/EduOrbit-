"""
Read-Only Query Selectors for HRPM Module.
"""
from django.db.models import Q, Count, Avg
from backend.apps.hr.models import (
    EmployeeProfile, JobRequisition, JobVacancy, JobApplication, InterviewPanel, InterviewScorecard, OfferLetter, OnboardingTask, HRSettings, LeaveType, LeavePolicy, LeaveRequest, LeaveBalance, PublicHoliday, LeaveEncashment
)

class EmployeeSelector:
    @staticmethod
    def get_all_employees(tenant, filters=None):
        qs = EmployeeProfile.objects.filter(tenant=tenant).select_related(
            'person', 'person__user'
        ).prefetch_related('assignment_history', 'onboarding_tasks', 'assigned_assets', 'leave_balances', 'objectives')
        
        if not filters:
            return qs
            
        if filters.get('status'):
            qs = qs.filter(status=filters['status'])
        if filters.get('department'):
            qs = qs.filter(assignment_history__department_name=filters['department'], assignment_history__is_active=True)
        if filters.get('employment_type'):
            qs = qs.filter(employment_type=filters['employment_type'])
        if filters.get('search'):
            search = filters['search']
            qs = qs.filter(
                Q(employee_number__icontains=search) |
                Q(person__first_name__icontains=search) |
                Q(person__last_name__icontains=search) |
                Q(person__user__email__icontains=search) |
                Q(job_title__icontains=search)
            ).distinct()
            
        return qs

    @staticmethod
    def get_employee_by_id(tenant, employee_id):
        return EmployeeProfile.objects.filter(tenant=tenant, id=employee_id).select_related('person', 'person__user').first()


class RecruitmentSelector:
    @staticmethod
    def get_requisitions(tenant, status=None):
        qs = JobRequisition.objects.filter(tenant=tenant).select_related('requested_by__person')
        if status:
            qs = qs.filter(status=status)
        return qs

    @staticmethod
    def get_vacancies(tenant, status=None):
        qs = JobVacancy.objects.filter(tenant=tenant).select_related('requisition')
        if status:
            qs = qs.filter(status=status)
        return qs

    @staticmethod
    def get_applications(tenant, vacancy_id=None, stage=None):
        qs = JobApplication.objects.filter(tenant=tenant).select_related('vacancy').prefetch_related('interview_scorecards')
        if vacancy_id:
            qs = qs.filter(vacancy_id=vacancy_id)
        if stage:
            qs = qs.filter(stage=stage)
        return qs


class OnboardingSelector:
    @staticmethod
    def get_tasks_for_employee(tenant, employee_id):
        return OnboardingTask.objects.filter(tenant=tenant, employee_id=employee_id).order_by('due_date')


class LeaveSelector:
    @staticmethod
    def get_leave_types(tenant):
        return LeaveType.objects.filter(tenant=tenant)

    @staticmethod
    def get_leave_requests(tenant, employee_id=None, status=None):
        qs = LeaveRequest.objects.filter(tenant=tenant).select_related('employee__person', 'leave_type')
        if employee_id:
            qs = qs.filter(employee_id=employee_id)
        if status:
            qs = qs.filter(status=status)
        return qs.order_by('-start_date')

    @staticmethod
    def get_employee_balances(tenant, employee_id):
        return LeaveBalance.objects.filter(tenant=tenant, employee_id=employee_id).select_related('leave_type')

    @staticmethod
    def get_public_holidays(tenant):
        return PublicHoliday.objects.filter(tenant=tenant).order_by('date')


class HRSettingsSelector:
    @staticmethod
    def get_tenant_settings(tenant):
        settings, _ = HRSettings.objects.get_or_create(tenant=tenant)
        return settings
