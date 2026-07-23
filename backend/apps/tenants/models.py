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
    Platform recurring subscription packages.
    """
    INTERVALS = [
        ('monthly', 'Monthly'),
        ('termly', 'Termly'),
        ('quarterly', 'Quarterly'),
        ('annual', 'Annual'),
        ('custom', 'Custom')
    ]
    name = models.CharField(max_length=100)
    interval = models.CharField(max_length=20, choices=INTERVALS, default='monthly')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='NGN')
    is_active = models.BooleanField(default=True)
    features = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.name} ({self.interval})"


class TenantSubscription(TenantBaseModel):
    """
    Licenses and active subscriptions per Tenant (Organization).
    """
    STATUS_CHOICES = [
        ('trial', 'Trial'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('expired', 'Expired')
    ]
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='trial')
    
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()
    grace_period_ends_at = models.DateTimeField(null=True, blank=True)
    
    # Module-based licensing system
    modules_licensed = models.JSONField(default=dict, blank=True, help_text="e.g. {'ai_tutor': {'enabled': true, 'expiry': '...'}}")
    renewal_history = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f"{self.tenant.name} - {self.plan.name if self.plan else 'Custom'} ({self.status})"

    def is_active_license(self) -> bool:
        if self.status == 'suspended':
            return False
        return self.end_date > timezone.now() or (self.grace_period_ends_at and self.grace_period_ends_at > timezone.now())


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
