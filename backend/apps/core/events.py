import logging
from typing import Dict, List, Callable, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger("eduorbit.events")

@dataclass
class DomainEvent:
    """
    Standard Base class for all transactional domain events.
    """
    event_name: str
    tenant_id: str
    actor_id: Optional[str] = None
    timestamp: str = None
    data: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_name": self.event_name,
            "tenant_id": self.tenant_id,
            "actor_id": self.actor_id,
            "timestamp": self.timestamp,
            "data": self.data or {}
        }


class DomainEventBus:
    """
    Enterprise Decoupled Event Bus supporting synchronous listeners and async Celery routing.
    """
    def __init__(self):
        self._handlers: Dict[str, List[Callable[[DomainEvent], None]]] = {}

    def subscribe(self, event_name: str, handler: Callable[[DomainEvent], None]):
        """
        Subscribe a handler to execute when event is published.
        """
        if event_name not in self._handlers:
            self._handlers[event_name] = []
        self._handlers[event_name].append(handler)
        logger.info(f"Registered subscriber {handler.__name__} for event '{event_name}'")

    def publish(self, event: DomainEvent):
        """
        Publish an event to all sync listeners and dispatch to background workers.
        """
        event_name = event.event_name
        handlers = self._handlers.get(event_name, [])
        
        logger.info(f"Dispatching event '{event_name}' (Tenant: {event.tenant_id})")
        
        # Execute registered synchronous callbacks
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Sync handler {handler.__name__} failed on event {event_name}: {str(e)}", exc_info=True)
                
        # Send task to Celery queue for asynchronous consumers
        try:
            from backend.apps.core.tasks import dispatch_async_event
            dispatch_async_event.delay(event_name, event.to_dict())
        except ImportError:
            pass
        except Exception as ex:
            logger.warning(f"Failed to queue event {event_name} asynchronously: {str(ex)}")


# Global event bus locator
event_bus = DomainEventBus()


# Enterprise Event Dictionary Catalog
class EduEvents:
    STUDENT_CREATED = "student.created"
    STUDENT_PROMOTED = "student.promoted"
    STUDENT_GRADUATED = "student.graduated"
    TEACHER_ASSIGNED = "teacher.assigned"
    ATTENDANCE_MARKED = "attendance.marked"
    INVOICE_GENERATED = "invoice.generated"
    PAYMENT_RECEIVED = "payment.received"
    SUBSCRIPTION_EXPIRED = "subscription.expired"
    EXAM_PUBLISHED = "exam.published"
    
    # Academic Configuration Events
    ACADEMIC_YEAR_CREATED = "academicyear.created"
    ACADEMIC_YEAR_ACTIVATED = "academicyear.activated"
    ACADEMIC_PERIOD_CREATED = "academicperiod.created"
    CURRICULUM_CREATED = "curriculum.created"
    CURRICULUM_UPDATED = "curriculum.updated"
    SUBJECT_ASSIGNED = "subject.assigned"
    SUBJECT_REMOVED = "subject.removed"
    CLASS_CREATED = "class.created"
    CLASS_ARCHIVED = "class.archived"
    GRADING_CONFIGURED = "grading.configured"
    ASSESSMENT_CONFIGURED = "assessment.configured"
    PROMOTION_POLICY_CHANGED = "promotionpolicy.changed"
    CALENDAR_PUBLISHED = "calendar.published"
