import uuid
from django.db import models
from django.utils import timezone
from backend.apps.core.models import TenantBaseModel
from backend.apps.hr.constants import REQUISITION_STATUS, VACANCY_STATUS, APPLICATION_STAGE, INTERVIEW_TYPE

class JobRequisition(TenantBaseModel):
    title = models.CharField(max_length=150)
    department = models.CharField(max_length=100)
    number_of_openings = models.IntegerField(default=1)
    reason = models.TextField(blank=True)
    requested_by = models.ForeignKey('hr.EmployeeProfile', on_delete=models.CASCADE, related_name='job_requisitions')
    status = models.CharField(max_length=30, choices=REQUISITION_STATUS, default='draft')
    workflow_instance = models.ForeignKey('workflow.WorkflowInstance', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.title} ({self.department})"


class JobVacancy(TenantBaseModel):
    requisition = models.ForeignKey(JobRequisition, on_delete=models.SET_NULL, null=True, blank=True, related_name='vacancies')
    title = models.CharField(max_length=150)
    description = models.TextField()
    department = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=30, choices=VACANCY_STATUS, default='published')
    closing_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.title


class JobApplication(TenantBaseModel):
    vacancy = models.ForeignKey(JobVacancy, on_delete=models.CASCADE, related_name='applications')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True)
    resume_url = models.CharField(max_length=255, blank=True)
    stage = models.CharField(max_length=30, choices=APPLICATION_STAGE, default='applied')
    ai_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    ai_summary = models.TextField(blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.stage})"


class InterviewPanel(TenantBaseModel):
    application = models.ForeignKey(JobApplication, on_delete=models.CASCADE, related_name='interviews')
    scheduled_at = models.DateTimeField(default=timezone.now)
    interview_type = models.CharField(max_length=30, choices=INTERVIEW_TYPE, default='in_person')
    location_link = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Interview: {self.application.first_name} on {self.scheduled_at}"


class InterviewScorecard(TenantBaseModel):
    application = models.ForeignKey(JobApplication, on_delete=models.CASCADE, related_name='interview_scorecards')
    interviewer = models.ForeignKey('hr.EmployeeProfile', on_delete=models.CASCADE)
    score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    feedback = models.TextField(blank=True)
    recommendation = models.CharField(max_length=50, default='recommend')  # recommend, reject, hold

    def __str__(self):
        return f"Scorecard: {self.application.first_name} ({self.score}/100)"


class OfferLetter(TenantBaseModel):
    application = models.ForeignKey(JobApplication, on_delete=models.CASCADE, related_name='offer_letters')
    offered_salary = models.DecimalField(max_digits=12, decimal_places=2)
    designation = models.CharField(max_length=150)
    start_date = models.DateField()
    status = models.CharField(max_length=30, default='draft')  # draft, sent, accepted, rejected

    def __str__(self):
        return f"Offer: {self.application.first_name} - {self.designation}"


class TalentPool(TenantBaseModel):
    email = models.EmailField()
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=50, blank=True)
    skills = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Talent Pool: {self.first_name} {self.last_name}"
