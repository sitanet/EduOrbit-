import uuid
from django.db import transaction
from django.utils import timezone
from backend.apps.hr.models import (
    JobRequisition, JobVacancy, JobApplication, InterviewPanel, InterviewScorecard, OfferLetter, TalentPool, HRAuditLog
)
from backend.apps.hr.services.employee import EmployeeService
from backend.apps.hr.validators import RecruitmentValidator
from backend.apps.core.events import event_bus, DomainEvent

class RecruitmentService:
    @staticmethod
    @transaction.atomic
    def create_requisition(tenant, requested_by_employee, title, department, number_of_openings=1, reason=""):
        req = JobRequisition.objects.create(
            tenant=tenant,
            requested_by=requested_by_employee,
            title=title,
            department=department,
            number_of_openings=number_of_openings,
            reason=reason,
            status='approved'  # Approved for default workflow
        )
        return req

    @staticmethod
    @transaction.atomic
    def publish_vacancy(tenant, title, department, description="", requisition=None, closing_date=None):
        RecruitmentValidator.validate_vacancy_dates(closing_date)
        vacancy = JobVacancy.objects.create(
            tenant=tenant,
            requisition=requisition,
            title=title,
            department=department,
            description=description,
            closing_date=closing_date,
            status='published'
        )
        return vacancy

    @staticmethod
    @transaction.atomic
    def submit_application(tenant, vacancy, first_name, last_name, email, phone="", resume_url=""):
        app = JobApplication.objects.create(
            tenant=tenant,
            vacancy=vacancy,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            resume_url=resume_url,
            stage='applied'
        )
        return app

    @staticmethod
    @transaction.atomic
    def schedule_interview(tenant, application, scheduled_at, interview_type='in_person', location_link=""):
        panel = InterviewPanel.objects.create(
            tenant=tenant,
            application=application,
            scheduled_at=scheduled_at,
            interview_type=interview_type,
            location_link=location_link
        )
        application.stage = 'interviewing'
        application.save()
        return panel

    @staticmethod
    @transaction.atomic
    def submit_scorecard(tenant, application, interviewer_employee, score, feedback="", recommendation="recommend"):
        RecruitmentValidator.validate_scorecard(score)
        card = InterviewScorecard.objects.create(
            tenant=tenant,
            application=application,
            interviewer=interviewer_employee,
            score=score,
            feedback=feedback,
            recommendation=recommendation
        )
        return card

    @staticmethod
    @transaction.atomic
    def generate_offer(tenant, application, offered_salary, designation, start_date):
        offer = OfferLetter.objects.create(
            tenant=tenant,
            application=application,
            offered_salary=offered_salary,
            designation=designation,
            start_date=start_date,
            status='sent'
        )
        application.stage = 'offered'
        application.save()
        return offer

    @staticmethod
    @transaction.atomic
    def hire_candidate(tenant, application, school=None, department_name='Academics', salary_grade='grade_1'):
        application.stage = 'hired'
        application.save()
        
        # Call EmployeeService
        employee = EmployeeService.create_employee(
            tenant=tenant,
            first_name=application.first_name,
            last_name=application.last_name,
            email=application.email,
            job_title=application.vacancy.title if application.vacancy else 'Teacher',
            salary_grade=salary_grade,
            school=school,
            department_name=department_name
        )
        
        # Publish Domain Events
        event1 = DomainEvent("candidate.hired", tenant_id=str(tenant.id), data={"id": str(application.id), "employee_id": str(employee.id)})
        event2 = DomainEvent("onboarding.started", tenant_id=str(tenant.id), data={"employee_id": str(employee.id)})
        transaction.on_commit(lambda: event_bus.publish(event1))
        transaction.on_commit(lambda: event_bus.publish(event2))
        
        return employee
