import uuid
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.contrib.postgres.indexes import GinIndex
from backend.apps.core.models.base import PlatformBaseModel

class OutboxStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    PROCESSING = 'PROCESSING', 'Processing'
    PROCESSED = 'PROCESSED', 'Processed'
    FAILED = 'FAILED', 'Failed'
    DEAD = 'DEAD', 'Dead'
    ARCHIVED = 'ARCHIVED', 'Archived'

class OutboxEvent(PlatformBaseModel):
    event_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    event_name = models.CharField(max_length=150)
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name="outbox_events",
        null=True,
        blank=True,
        db_index=True
    )
    aggregate_type = models.CharField(max_length=100)
    aggregate_id = models.CharField(max_length=100)
    aggregate_version = models.IntegerField(default=1)
    sequence_number = models.BigIntegerField(default=1)
    payload = models.JSONField()  # Standardized payload schema
    payload_schema_version = models.IntegerField(default=1)
    occurred_at = models.DateTimeField(default=timezone.now)
    initiated_by = models.CharField(max_length=100, null=True, blank=True)
    correlation_id = models.CharField(max_length=100, null=True, blank=True)
    causation_id = models.CharField(max_length=100, null=True, blank=True)
    
    # State, lock & telemetry timestamps tracking
    status = models.CharField(max_length=20, choices=OutboxStatus.choices, default=OutboxStatus.PENDING, db_index=True)
    published_to_broker_at = models.DateTimeField(null=True, blank=True)
    dispatched_at = models.DateTimeField(null=True, blank=True)
    processing_started_at = models.DateTimeField(null=True, blank=True)
    processing_completed_at = models.DateTimeField(null=True, blank=True)
    dispatch_attempts = models.IntegerField(default=0)
    next_retry_at = models.DateTimeField(null=True, blank=True)
    locked_at = models.DateTimeField(null=True, blank=True)
    locked_by = models.CharField(max_length=255, null=True, blank=True)  # UUID or hostname:pid
    worker_hostname = models.CharField(max_length=150, null=True, blank=True)
    worker_pid = models.IntegerField(null=True, blank=True)
    last_error = models.TextField(null=True, blank=True)

    # Broker troubleshooting metadata
    broker_name = models.CharField(max_length=50, null=True, blank=True)
    exchange = models.CharField(max_length=100, null=True, blank=True)
    routing_key = models.CharField(max_length=100, null=True, blank=True)
    queue_name = models.CharField(max_length=100, null=True, blank=True)
    message_id = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(check=Q(dispatch_attempts__gte=0), name='outbox_dispatch_attempts_gte_0'),
            models.CheckConstraint(check=Q(payload_schema_version__gte=1), name='outbox_payload_schema_version_gte_1'),
            models.CheckConstraint(check=Q(sequence_number__gte=1), name='outbox_sequence_number_gte_1'),
            models.UniqueConstraint(fields=['event_id'], name='outbox_unique_event_id'),
        ]
        indexes = [
            GinIndex(fields=['payload'], name='outbox_payload_gin'),
            models.Index(fields=['next_retry_at'], name='outbox_pending_retry_idx', condition=Q(status__in=['PENDING', 'FAILED'])),
            models.Index(fields=['status', 'locked_at'], name='outbox_status_locked_idx'),
            models.Index(fields=['occurred_at'], name='outbox_occurred_at_idx'),
            models.Index(fields=['aggregate_type', 'aggregate_id', 'sequence_number'], name='outbox_aggregate_seq_idx'),
            models.Index(fields=['tenant', 'correlation_id'], name='outbox_tenant_corr_idx'),
        ]
