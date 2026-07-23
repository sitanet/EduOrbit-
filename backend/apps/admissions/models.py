import uuid
from django.db import models
from django.utils import timezone
from backend.apps.core.models import TenantBaseModel, PlatformBaseModel

# ==============================================================
# CAMPAIGN & INTAKE MODELS
# ==============================================================

class AdmissionCampaign(TenantBaseModel):
    """
    Admission Campaign scoped by school and linked to academic years (e.g. 2027/2028 Admissions).
    """
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE, related_name='admission_campaigns')
    academic_year = models.ForeignKey('academic.AcademicYear', on_delete=models.CASCADE)
    name = models.CharField(max_length=150)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True, db_index=True)

    def __str__(self):
        return f"{self.name} ({self.school.name})"


class AdmissionIntake(TenantBaseModel):
    """
    Intake cohorts within a campaign (e.g. First Batch, Transfer Intake).
    """
    campaign = models.ForeignKey(AdmissionCampaign, on_delete=models.CASCADE, related_name='intakes')
    name = models.CharField(max_length=100)  # e.g., Mid-Year Intake
    status = models.CharField(max_length=20, default='open')  # open, closed

    def __str__(self):
        return f"{self.name} - {self.campaign.name}"


# ==============================================================
# APPLICANT & APPLICATION MODELS
# ==============================================================

class Applicant(TenantBaseModel):
    """
    Applicant entry linking back to unified base Person profile details.
    Allows multiple historic applications over seasons.
    """
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE)
    person = models.ForeignKey('people.Person', on_delete=models.CASCADE, related_name='applicants')
    applicant_number = models.CharField(max_length=50, unique=True, db_index=True)

    def __str__(self):
        return f"{self.person.first_name} {self.person.last_name} ({self.applicant_number})"


# ==============================================================
# REUSABLE FORMS ENGINE SCHEMAS
# ==============================================================

class FormDefinition(TenantBaseModel):
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE)
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class FormSection(TenantBaseModel):
    form = models.ForeignKey(FormDefinition, on_delete=models.CASCADE, related_name='sections')
    name = models.CharField(max_length=100)
    order = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.name} - {self.form.name}"


class FormField(TenantBaseModel):
    section = models.ForeignKey(FormSection, on_delete=models.CASCADE, related_name='fields')
    label = models.CharField(max_length=150)
    field_type = models.CharField(max_length=30, default='text')  # text, select, file, number
    required = models.BooleanField(default=False)
    order = models.IntegerField(default=1)

    def __str__(self):
        return self.label


class FormSubmission(TenantBaseModel):
    form = models.ForeignKey(FormDefinition, on_delete=models.CASCADE)
    submitted_data = models.JSONField(default=dict)

    def __str__(self):
        return f"Submission #{self.id} for {self.form.name}"


# ==============================================================
# ADMISSION APPLICATIONS & DOCUMENTS
# ==============================================================

class AdmissionApplication(TenantBaseModel):
    """
    Form application entries linking applicants, intakes, and dynamic submissions data.
    """
    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('waitlisted', 'Waitlisted'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('enrolled', 'Enrolled')
    ]
    intake = models.ForeignKey(AdmissionIntake, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE, related_name='applications')
    target_level = models.ForeignKey('academic.AcademicLevel', on_delete=models.CASCADE)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')
    current_stage = models.CharField(max_length=50, default='application')
    
    submission = models.OneToOneField(FormSubmission, on_delete=models.SET_NULL, null=True, blank=True)
    application_date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"App for {self.applicant.applicant_number} ({self.status})"


class ApplicationDocument(TenantBaseModel):
    """
    Application-specific attached files requiring verification checks.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('requires_resubmission', 'Requires Resubmission')
    ]
    application = models.ForeignKey(AdmissionApplication, on_delete=models.CASCADE, related_name='documents')
    document_type = models.ForeignKey('people.DocumentType', on_delete=models.CASCADE)
    document_file = models.CharField(max_length=255)
    verification_status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.document_type.name} - Application #{self.application.id}"


# ==============================================================
# ASSESSMENTS, OFFERS, AND WAITLISTS
# ==============================================================

class AdmissionAssessment(TenantBaseModel):
    """
    Entrance screening marks (Written Tests, Practical Reviews).
    """
    application = models.ForeignKey(AdmissionApplication, on_delete=models.CASCADE, related_name='assessments')
    assessment_type = models.CharField(max_length=30, default='written_test')  # written_test, interview, practical
    scheduled_time = models.DateTimeField()
    score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    remarks = models.TextField(blank=True)

    def __str__(self):
        return f"{self.assessment_type} - {self.application.applicant.applicant_number}"


class AdmissionOffer(TenantBaseModel):
    """
    System offers templates and acceptance statuses.
    """
    STATUS = [
        ('issued', 'Offer Issued'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired')
    ]
    application = models.OneToOneField(AdmissionApplication, on_delete=models.CASCADE, related_name='offer')
    status = models.CharField(max_length=20, choices=STATUS, default='issued')
    acceptance_deadline = models.DateField()
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Offer for {self.application.applicant.applicant_number} ({self.status})"


class AdmissionWaitlist(TenantBaseModel):
    """
    Waitlist queues mapping priorities.
    """
    application = models.OneToOneField(AdmissionApplication, on_delete=models.CASCADE, related_name='waitlist')
    position = models.IntegerField()
    priority = models.CharField(max_length=20, default='medium')

    def __str__(self):
        return f"Waitlist #{self.position} - {self.application.applicant.applicant_number}"


# ==============================================================
# SCHOLARSHIPS PLACEMENTS
# ==============================================================

class ScholarshipType(PlatformBaseModel):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class ScholarshipAward(TenantBaseModel):
    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE, related_name='scholarship_awards')
    scholarship_type = models.ForeignKey(ScholarshipType, on_delete=models.CASCADE)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Award {self.scholarship_type.name} to {self.applicant.applicant_number}"
