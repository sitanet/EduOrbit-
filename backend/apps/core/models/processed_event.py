from django.db import models
from backend.apps.core.models.base import PlatformBaseModel

class ProcessedEvent(PlatformBaseModel):
    event_id = models.UUIDField(unique=True, db_index=True)
    consumer_name = models.CharField(max_length=150)
    processed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['event_id', 'consumer_name'], name='unique_processed_event_consumer'),
        ]
