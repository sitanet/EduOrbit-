from django.db import transaction
from backend.apps.core.models.outbox import OutboxEvent

class OutboxService:
    @staticmethod
    @transaction.atomic
    def record_event(tenant, event_name, aggregate_type, aggregate_id, payload, correlation_id=None, causation_id=None, initiated_by=None, schema_version=1):
        # Lock current max sequence_number for this aggregate to ensure atomic sequential ordering
        last_event = OutboxEvent.objects.select_for_update().filter(
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id
        ).order_by('-sequence_number').first()
        
        next_seq = (last_event.sequence_number + 1) if last_event else 1
        
        event = OutboxEvent.objects.create(
            tenant=tenant,
            event_name=event_name,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            sequence_number=next_seq,
            payload=payload,
            correlation_id=correlation_id,
            causation_id=causation_id,
            initiated_by=initiated_by,
            payload_schema_version=schema_version
        )
        
        # Trigger outbox processing task after commit (resilient to broker failure)
        def trigger():
            try:
                from backend.apps.core.tasks import process_pending_outbox
                process_pending_outbox.delay()
            except Exception as ex:
                import logging
                logger = logging.getLogger("eduorbit.outbox")
                logger.warning(f"Failed to queue outbox processing task: {ex}")
            
        transaction.on_commit(trigger)
        return event
