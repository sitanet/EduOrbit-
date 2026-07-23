from django.db import models
from backend.apps.core.models import TenantBaseModel

class AuditLogEntry(TenantBaseModel):
    """
    Enterprise Security Audit Log Entry capturing row-level changes and user details.
    """
    user_id = models.UUIDField(null=True, blank=True, db_index=True)
    action = models.CharField(max_length=100, db_index=True)  # E.g. 'STUDENT_CREATED', 'FEES_PAID'
    resource_type = models.CharField(max_length=100, db_index=True)  # E.g. 'Student', 'Invoice'
    resource_id = models.UUIDField(null=True, blank=True, db_index=True)
    
    # Audit diff changes tracking
    before_state = models.JSONField(default=dict, blank=True)
    after_state = models.JSONField(default=dict, blank=True)
    
    # Client request metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True, db_index=True)
    user_agent = models.TextField(blank=True)
    device_type = models.CharField(max_length=50, blank=True)  # Mobile, Tablet, Desktop
    browser_type = models.CharField(max_length=50, blank=True)  # Chrome, Safari, Firefox
    
    reason = models.TextField(blank=True, help_text="Reason for modification if provided by actor")

    class Meta:
        verbose_name = "Audit Log Entry"
        verbose_name_plural = "Audit Log Entries"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.action} on {self.resource_type} ({self.resource_id}) by User {self.user_id}"
