"""
Validation Rules for HRPM Module.
"""
from django.core.exceptions import ValidationError
from django.utils import timezone

class EmployeeValidator:
    @staticmethod
    def validate_employee_number(employee_number, tenant, instance_id=None):
        from backend.apps.hr.models.employee import EmployeeProfile
        qs = EmployeeProfile.objects.filter(tenant=tenant, employee_number=employee_number)
        if instance_id:
            qs = qs.exclude(id=instance_id)
        if qs.exists():
            raise ValidationError(f"Employee number '{employee_number}' is already assigned in this school organization.")

    @staticmethod
    def validate_email_uniqueness(email, tenant, instance_id=None):
        from backend.apps.people.models import Person
        qs = Person.objects.filter(tenant=tenant, user__email=email)
        if instance_id:
            qs = qs.exclude(employee_profile__id=instance_id)
        if qs.exists():
            raise ValidationError(f"Email '{email}' is already associated with an existing person record in this tenant.")


class RecruitmentValidator:
    @staticmethod
    def validate_vacancy_dates(closing_date):
        if closing_date and closing_date < timezone.now().date():
            raise ValidationError("Vacancy closing date cannot be set in the past.")

    @staticmethod
    def validate_scorecard(score):
        if score < 0 or score > 100:
            raise ValidationError("Interview scorecard score must be between 0.00 and 100.00.")


class OnboardingValidator:
    @staticmethod
    def validate_due_date(due_date):
        if due_date and due_date < timezone.now().date():
            raise ValidationError("Onboarding task due date cannot be in the past.")


class LeaveValidator:
    @staticmethod
    def validate_leave_dates(start_date, end_date):
        if end_date < start_date:
            raise ValidationError("Leave end date cannot be earlier than start date.")

    @staticmethod
    def validate_leave_balance(remaining_days, requested_days):
        if requested_days > remaining_days:
            raise ValidationError(f"Insufficient leave balance. Requested {requested_days} days, but only {remaining_days} days remaining.")


class PayrollValidator:
    @staticmethod
    def validate_salary_amount(amount):
        if amount is not None and amount < 0:
            raise ValidationError("Salary amount cannot be negative.")
