import uuid
from django.db import models
from django.utils import timezone
from backend.apps.core.models import TenantBaseModel
from backend.apps.hr.constants import EMPLOYEE_STATUS, EMPLOYMENT_TYPE, CONFIRMATION_STATUS, EMPLOYEE_LIFECYCLE_STATUS
from backend.apps.core.storage import generate_scoped_upload_path


def employee_photo_path(instance, filename):
    ext = filename.split('.')[-1]
    emp_num = getattr(instance, 'employee_number', 'unknown')
    tenant_id = str(instance.tenant_id if hasattr(instance, 'tenant_id') and instance.tenant_id else 'global')
    return generate_scoped_upload_path(
        tenant_id=tenant_id,
        school_id='hr',
        academic_year=timezone.now().year,
        module='employee_photos',
        filename=f"photo_{emp_num}_{uuid.uuid4().hex[:8]}.{ext}"
    )


def employee_thumb_path(instance, filename):
    ext = filename.split('.')[-1]
    emp_num = getattr(instance, 'employee_number', 'unknown')
    tenant_id = str(instance.tenant_id if hasattr(instance, 'tenant_id') and instance.tenant_id else 'global')
    return generate_scoped_upload_path(
        tenant_id=tenant_id,
        school_id='hr',
        academic_year=timezone.now().year,
        module='employee_thumbnails',
        filename=f"thumb_{emp_num}_{uuid.uuid4().hex[:8]}.{ext}"
    )


def employee_original_path(instance, filename):
    ext = filename.split('.')[-1]
    emp_num = getattr(instance, 'employee_number', 'unknown')
    tenant_id = str(instance.tenant_id if hasattr(instance, 'tenant_id') and instance.tenant_id else 'global')
    return generate_scoped_upload_path(
        tenant_id=tenant_id,
        school_id='hr',
        academic_year=timezone.now().year,
        module='employee_originals',
        filename=f"original_{emp_num}_{uuid.uuid4().hex[:8]}.{ext}"
    )


class EmployeeProfile(TenantBaseModel):
    """
    Extends the PMC base Person model with HR-specific parameters without duplicating demographics.
    """
    person = models.OneToOneField('people.Person', on_delete=models.CASCADE, related_name='employee_profile')
    employee_number = models.CharField(max_length=100, unique=True)
    job_title = models.CharField(max_length=150)
    salary_grade = models.CharField(max_length=50, default='grade_1')
    status = models.CharField(max_length=30, choices=EMPLOYEE_STATUS, default='active')
    lifecycle_status = models.CharField(max_length=50, choices=EMPLOYEE_LIFECYCLE_STATUS, default='active')
    employment_type = models.CharField(max_length=30, choices=EMPLOYMENT_TYPE, default='full_time')
    confirmation_status = models.CharField(max_length=30, choices=CONFIRMATION_STATUS, default='probation')
    joined_date = models.DateField(default=timezone.now)
    probation_end_date = models.DateField(null=True, blank=True)
    
    # 7-Tier Organizational Structure & Cost Centre
    company_name = models.CharField(max_length=150, default='EduOrbit Group')
    campus_name = models.CharField(max_length=150, default='Main Campus')
    division_name = models.CharField(max_length=150, blank=True)
    directorate_name = models.CharField(max_length=150, blank=True)
    department_name = models.CharField(max_length=150, default='General Academics')
    unit_name = models.CharField(max_length=150, blank=True)
    team_name = models.CharField(max_length=150, blank=True)
    cost_centre = models.CharField(max_length=100, default='CC-101-ACADEMICS')

    # Banking Details
    bank_name = models.CharField(max_length=150, blank=True)
    account_number = models.CharField(max_length=50, blank=True)
    account_name = models.CharField(max_length=150, blank=True)
    sort_code_iban = models.CharField(max_length=50, blank=True)

    # Statutory PII Encrypted Storage
    nin_encrypted = models.TextField(blank=True, null=True)
    bvn_encrypted = models.TextField(blank=True, null=True)
    rsa_pin_encrypted = models.TextField(blank=True, null=True)
    tax_id_encrypted = models.TextField(blank=True, null=True)
    pfa_name = models.CharField(max_length=150, blank=True)
    is_nin_verified = models.BooleanField(default=False)
    is_bvn_verified = models.BooleanField(default=False)
    kyc_verification_meta = models.JSONField(default=dict, blank=True)
    
    # Statutory Contributions (Step 3 - Nigerian Compliance)
    nhf_number = models.CharField(max_length=50, blank=True, help_text="National Housing Fund (FMBN) contribution ID")
    nhis_number = models.CharField(max_length=50, blank=True, help_text="National Health Insurance Scheme ID")
    nsitf_number = models.CharField(max_length=50, blank=True, help_text="Nigeria Social Insurance Trust Fund (Employee Compensation) ID")

    # Enterprise Photo Management (Single Active Photo Engine - Phase 12.4.4A)
    photo = models.ImageField(upload_to=employee_photo_path, null=True, blank=True)
    photo_thumbnail = models.ImageField(upload_to=employee_thumb_path, null=True, blank=True)
    original_photo = models.ImageField(upload_to=employee_original_path, null=True, blank=True)
    photo_hash = models.CharField(max_length=64, blank=True, null=True, help_text="SHA256 checksum of processed active photo")
    photo_width = models.IntegerField(null=True, blank=True)
    photo_height = models.IntegerField(null=True, blank=True)
    photo_size = models.IntegerField(null=True, blank=True, help_text="Active photo size in bytes")
    photo_source = models.CharField(max_length=30, default='HR_UPLOAD', blank=True)
    photo_status = models.CharField(max_length=20, default='ACTIVE', blank=True)
    photo_verification_provider = models.CharField(max_length=50, blank=True, null=True)
    photo_verification_method = models.CharField(max_length=50, blank=True, null=True)
    photo_verification_reference = models.CharField(max_length=100, blank=True, null=True)
    photo_processing_metrics = models.JSONField(default=dict, blank=True, help_text="Processing time, compression ratio, telemetry")
    photo_verified_at = models.DateTimeField(null=True, blank=True)
    photo_last_updated = models.DateTimeField(null=True, blank=True)
    photo_updated_by = models.ForeignKey('people.Person', on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_employee_photos')
    photo_replacement_reason = models.TextField(blank=True, null=True)
    
    # Next of Kin & Emergency Contacts
    next_of_kin_name = models.CharField(max_length=150, blank=True)
    next_of_kin_relationship = models.CharField(max_length=100, blank=True)
    next_of_kin_phone = models.CharField(max_length=50, blank=True)
    emergency_contact_phone = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"{self.employee_number}: {self.person.first_name} {self.person.last_name}"


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


class HRAuditLog(TenantBaseModel):
    actor = models.ForeignKey('people.Person', on_delete=models.SET_NULL, null=True, blank=True)
    event_type = models.CharField(max_length=100)
    model_affected = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100, blank=True)
    old_values = models.JSONField(default=dict, blank=True)
    new_values = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    reason = models.TextField(blank=True)

    def __str__(self):
        return f"{self.event_type} on {self.model_affected} ({self.created_at})"
