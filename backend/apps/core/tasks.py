import logging
from celery import shared_task

logger = logging.getLogger("eduorbit.tasks")

@shared_task(name="core.dispatch_async_event")
def dispatch_async_event(event_type: str, event_data: dict):
    """
    Asynchronously handle dispatched events in Celery workers.
    Allows downstream integrations, notifications, and AI processing to execute out of process.
    """
    logger.info(f"Received async event task '{event_type}' with data payload: {event_data}")
    # Event routing logic can be expanded here dynamically
    return True
