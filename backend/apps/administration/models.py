import uuid
from django.db import models
from django.utils import timezone
from backend.apps.core.models import TenantBaseModel, PlatformBaseModel

# ==============================================================
# PLATFORM SETTINGS & SUBSCRIPTION PLANS
# ==============================================================

class PlatformSetting(PlatformBaseModel):
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()

    def __str__(self):
        return self.key


class SchoolSetting(TenantBaseModel):
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE, related_name='settings')
    theme_color = models.CharField(max_length=50, default='#1e3a8a')
    motto = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Settings for {self.school.name}"


class SubscriptionPlan(PlatformBaseModel):
    name = models.CharField(max_length=150)
    monthly_price = models.DecimalField(max_digits=12, decimal_places=2)
    student_limit = models.IntegerField(default=100)

    def __str__(self):
        return f"{self.name} (₦{self.monthly_price}/mo)"


# ==============================================================
# SUBSCRIPTIONS & LICENSES LIFECYCLES
# ==============================================================

class SchoolSubscription(TenantBaseModel):
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT)
    expiry_date = models.DateField()

    def __str__(self):
        return f"{self.school.name} Subscription to {self.plan.name}"


class ModuleLicense(TenantBaseModel):
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE, related_name='licenses')
    module_name = models.CharField(max_length=100)  # e.g., hostel, clinic, inventory
    is_enabled = models.BooleanField(default=True)

    def __str__(self):
        return f"License: {self.module_name} for {self.school.name} ({'Active' if self.is_enabled else 'Suspended'})"


class FeatureFlag(TenantBaseModel):
    flag_name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.flag_name}: {'Enabled' if self.is_active else 'Disabled'}"


# ==============================================================
# WHITE LABELING, AUDITS & API KEYS
# ==============================================================

class SchoolBranding(TenantBaseModel):
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE, related_name='brandings')
    custom_domain = models.CharField(max_length=255, blank=True)
    logo_path = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Branding for {self.school.name}"


class PlatformAudit(PlatformBaseModel):
    """
    Immutable global operational audit log trail.
    """
    actor = models.ForeignKey('identity.User', on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=150)
    details = models.TextField(blank=True)
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Audit Log: {self.action} at {self.timestamp}"


class APIKey(TenantBaseModel):
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE, related_name='api_keys')
    token_key = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"API Key for {self.school.name}"
