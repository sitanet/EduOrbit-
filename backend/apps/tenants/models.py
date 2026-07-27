import uuid
from django.db import models
from django.utils import timezone
from backend.apps.core.models import PlatformBaseModel, TenantBaseModel

# ==============================================================
# TENANT & SCHOOL SCHEMAS
# ==============================================================

class Tenant(PlatformBaseModel):
    """
    Tenant Organization representing the corporate group (e.g., Grace Education Group).
    Accounts are mapped at the organization level.
    """
    BILLING_MODELS = [
        ('school_pays', 'Model A (School Pays)'),
        ('parents_pay', 'Model B (Parents Pay)'),
        ('hybrid', 'Model C (Hybrid Billing)')
    ]
    name = models.CharField(max_length=255)
    legal_name = models.CharField(max_length=255, blank=True)
    registration_number = models.CharField(max_length=100, blank=True)
    tax_number = models.CharField(max_length=100, blank=True)
    
    # Billing Setup
    billing_model = models.CharField(max_length=20, choices=BILLING_MODELS, default='school_pays')
    
    # Branding configurations (white-label details)
    branding_config = models.JSONField(default=dict, blank=True)
    # Storage settings overrides (inherit S3/GCS or local)
    settings_override = models.JSONField(default=dict, blank=True)
    
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name = 'Tenant'
        verbose_name_plural = 'Tenants'

    def __str__(self):
        return self.name


class School(TenantBaseModel):
    """
    Specific Educational Institution under an Organization (Tenant).
    (e.g., Grace Nursery School, Grace College).
    """
    name = models.CharField(max_length=255)
    school_types = models.JSONField(default=list, help_text="e.g. ['creche', 'preschool', 'secondary']")
    curriculum_codes = models.JSONField(default=list, help_text="List of curriculum codes: ['nigerian', 'cambridge']")
    is_active = models.BooleanField(default=True, db_index=True)

    def __str__(self):
        return f"{self.name} ({self.tenant.name})"


# ==============================================================
# CAMPUS & BRANCH SCHEMAS
# ==============================================================

class Campus(TenantBaseModel):
    """
    Campus location under a specific School.
    """
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='campuses')
    name = models.CharField(max_length=255)
    address = models.TextField()
    contact_phone = models.CharField(max_length=30, blank=True)
    contact_email = models.EmailField(blank=True)
    principal_user_id = models.UUIDField(null=True, blank=True)
    branding_override = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.name} - {self.school.name}"


class Branch(TenantBaseModel):
    """
    Sub-branch location under a specific Campus.
    """
    campus = models.ForeignKey(Campus, on_delete=models.CASCADE, related_name='branches')
    name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name} - {self.campus.name}"


# ==============================================================
# SUBSCRIPTION & BILLING SCHEMAS
# ==============================================================

class SubscriptionPlan(PlatformBaseModel):
    """
    Platform recurring subscription packages supporting School Pay, Parent Pay, and Hybrid models.
    """
    BILLING_MODELS = [
        ('SCHOOL_PAY', 'School Pay'),
        ('PARENT_PAY', 'Parent Pay'),
        ('HYBRID', 'Hybrid')
    ]
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    billing_model = models.CharField(max_length=20, choices=BILLING_MODELS, default='SCHOOL_PAY')
    
    monthly_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    termly_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    yearly_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    trial_days = models.IntegerField(default=14)
    grace_period_days = models.IntegerField(default=7)
    max_students = models.IntegerField(default=500)
    max_staff = models.IntegerField(default=50)
    max_campuses = models.IntegerField(default=1)
    
    parent_portal_enabled = models.BooleanField(default=True)
    mobile_app_enabled = models.BooleanField(default=True)
    lms_enabled = models.BooleanField(default=True)
    cbt_enabled = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    features = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.name} ({self.billing_model})"


class TenantSubscription(TenantBaseModel):
    """
    Licenses and active subscriptions per Tenant (Organization).
    """
    STATUS_CHOICES = [
        ('TRIAL', 'Trial'),
        ('ACTIVE', 'Active'),
        ('GRACE', 'Grace Period'),
        ('EXPIRED', 'Expired'),
        ('SUSPENDED', 'Suspended'),
        ('CANCELLED', 'Cancelled')
    ]
    BILLING_CYCLES = [
        ('MONTHLY', 'Monthly'),
        ('TERMLY', 'Termly'),
        ('YEARLY', 'Yearly')
    ]
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE, null=True, blank=True)
    billing_model = models.CharField(max_length=20, default='SCHOOL_PAY')
    billing_cycle = models.CharField(max_length=20, choices=BILLING_CYCLES, default='MONTHLY')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='TRIAL')
    
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()
    grace_period_ends_at = models.DateTimeField(null=True, blank=True)
    auto_renew = models.BooleanField(default=True)
    payment_provider = models.CharField(max_length=50, default='OPay')
    
    modules_licensed = models.JSONField(default=dict, blank=True)
    renewal_history = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f"{self.tenant.name} - {self.plan.name if self.plan else 'Custom'} ({self.status})"

    def is_active_license(self) -> bool:
        if self.status in ['SUSPENDED', 'CANCELLED']:
            return False
        return self.end_date > timezone.now() or (self.grace_period_ends_at and self.grace_period_ends_at > timezone.now())


class StudentPlatformSubscription(TenantBaseModel):
    """
    Direct parent platform subscription for PARENT_PAY and HYBRID billing models.
    """
    student = models.ForeignKey('people.StudentProfile', on_delete=models.CASCADE, related_name='platform_subscriptions')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    billing_cycle = models.CharField(max_length=20, default='MONTHLY')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    paid_until = models.DateTimeField()
    payment_status = models.CharField(max_length=20, default='ACTIVE')  # ACTIVE, EXPIRED
    payment_reference = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Parent Subscription: {self.student.student_number} ({self.payment_status})"


# ==============================================================
# CUSTOM DOMAIN SCHEMAS
# ==============================================================

class CustomDomain(TenantBaseModel):
    """
    Verified custom web domains pointing to this tenant.
    """
    domain_name = models.CharField(max_length=255, unique=True, db_index=True)
    is_verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=100, default=uuid.uuid4)
    ssl_active = models.BooleanField(default=False)

    def __str__(self):
        return self.domain_name
