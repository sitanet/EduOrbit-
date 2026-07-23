from django.db import models
from backend.apps.core.models import PlatformBaseModel, TenantBaseModel

class PlatformConfiguration(PlatformBaseModel):
    """
    Global system settings configurations (e.g. platform domain, limits).
    """
    key = models.CharField(max_length=100, unique=True, db_index=True)
    value = models.JSONField(default=dict)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.key

class TenantConfiguration(TenantBaseModel):
    """
    Tenant-specific configuration parameters (e.g. timezone overrides, localization, grading preferences).
    """
    key = models.CharField(max_length=100, db_index=True)
    value = models.JSONField(default=dict)

    class Meta:
        unique_together = ('tenant', 'key')
        verbose_name = "Tenant Configuration"
        verbose_name_plural = "Tenant Configurations"

    def __str__(self):
        return f"{self.tenant.name} - {self.key}"

class FeatureToggle(PlatformBaseModel):
    """
    Global and Tenant-level feature flag manager controls (e.g. 'AI Tutor Enabled', 'Clinic Enabled').
    """
    name = models.CharField(max_length=100, unique=True, db_index=True)
    is_globally_enabled = models.BooleanField(default=False)
    enabled_tenant_ids = models.JSONField(default=list, blank=True, help_text="List of Tenant UUIDs explicitly whitelisted")
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class ThemeSetting(TenantBaseModel):
    """
    Branding settings configuration for each tenant school (colors, logos, fonts overrides).
    """
    primary_color = models.CharField(max_length=20, default="#2E7D32")
    secondary_color = models.CharField(max_length=20, default="#EF6C00")
    custom_css = models.TextField(blank=True)

    def __str__(self):
        return f"{self.tenant.name} - Theme"

class PaymentConfiguration(PlatformBaseModel):
    """
    Platform-level third party payment gateway configs and active adapter profiles.
    """
    gateway_name = models.CharField(max_length=50, unique=True, db_index=True)
    is_active = models.BooleanField(default=False)
    config = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.gateway_name

class AIConfiguration(PlatformBaseModel):
    """
    AI provider details and api access routes.
    """
    provider_name = models.CharField(max_length=50, unique=True, db_index=True)
    is_active = models.BooleanField(default=False)
    config = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.provider_name

class Curriculum(PlatformBaseModel):
    """
    Global repository of supported academic curricula (Nigerian, Cambridge, IB, Montessori, etc.).
    Keeps academic grading structures extensible.
    """
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True, db_index=True) # e.g. 'cambridge', 'nigerian'
    description = models.TextField(blank=True)
    grading_structure_meta = models.JSONField(default=dict, blank=True, help_text="Default grading and assessment scale blueprints")

    def __str__(self):
        return self.name
