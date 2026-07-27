import uuid
from django.db import models
from django.utils import timezone
from backend.apps.core.models import TenantBaseModel, PlatformBaseModel

# ==============================================================
# INTEGRATION PROVIDERS & EXTERNAL CONNECTORS
# ==============================================================

class IntegrationProvider(PlatformBaseModel):
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=50)  # auth, storage, payment, messaging, video
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.category})"


class APIClient(TenantBaseModel):
    client_name = models.CharField(max_length=150)
    client_key = models.CharField(max_length=100, unique=True)
    client_secret_hash = models.CharField(max_length=255)
    rate_limit_per_minute = models.IntegerField(default=60)
    scopes = models.TextField(default="read,write")

    def __str__(self):
        return f"API Client: {self.client_name}"


# ==============================================================
# WEBHOOKS & DOMAIN EVENT BUS
# ==============================================================

class WebhookEndpoint(TenantBaseModel):
    target_url = models.CharField(max_length=255)
    secret_key = models.CharField(max_length=100)
    events_subscribed = models.TextField(default="student.enrolled,invoice.paid")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Webhook: {self.target_url}"


class WebhookEvent(TenantBaseModel):
    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('retrying', 'Retrying')
    ]
    endpoint = models.ForeignKey(WebhookEndpoint, on_delete=models.CASCADE, related_name='events')
    event_type = models.CharField(max_length=100)
    payload_json = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')
    retry_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Event: {self.event_type} to {self.endpoint.target_url} ({self.status})"


# ==============================================================
# WORKFLOW AUTOMATION & SCHEDULER
# ==============================================================

class AutomationWorkflow(TenantBaseModel):
    name = models.CharField(max_length=150)
    trigger_event = models.CharField(max_length=100)  # e.g., student.enrolled, invoice.paid
    action_type = models.CharField(max_length=100)   # create_lms_account, notify_parents
    is_enabled = models.BooleanField(default=True)

    def __str__(self):
        return f"Workflow: {self.name} ({self.trigger_event})"


class ScheduledJob(TenantBaseModel):
    name = models.CharField(max_length=150)
    cron_expression = models.CharField(max_length=50, default="0 0 * * *")
    task_name = models.CharField(max_length=150)
    last_run_at = models.DateTimeField(null=True, blank=True)
    next_run_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Job: {self.name} ({self.cron_expression})"


class SyncConfiguration(TenantBaseModel):
    external_system = models.CharField(max_length=100)  # Google Workspace, M365
    entity_type = models.CharField(max_length=100)      # Student, Staff
    sync_direction = models.CharField(max_length=30, default='bi_directional')

    def __str__(self):
        return f"Sync: {self.external_system} ({self.entity_type})"


class IntegrationLog(TenantBaseModel):
    provider_name = models.CharField(max_length=100)
    action = models.CharField(max_length=100)
    status_code = models.IntegerField(default=200)
    latency_ms = models.IntegerField(default=0)
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Log: {self.provider_name} {self.action} ({self.status_code})"
