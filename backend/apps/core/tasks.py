import logging
import socket
import os
import random
from celery import shared_task
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.db.models import Q
from backend.apps.core.models.outbox import OutboxEvent, OutboxStatus

logger = logging.getLogger("eduorbit.tasks")

@shared_task(name="core.dispatch_async_event")
def dispatch_async_event(event_type: str, event_data: dict):
    """
    Asynchronously handle dispatched events in Celery workers.
    """
    logger.info(f"Received async event task '{event_type}' with data payload: {event_data}")
    return True

@shared_task(name="core.process_pending_outbox")
def process_pending_outbox():
    """
    Poll pending and failed outbox events in batch using SELECT FOR UPDATE SKIP LOCKED.
    Executes broker dispatching with exponential retry backoff and randomized jitter.
    """
    batch_size = getattr(settings, 'OUTBOX_BATCH_SIZE', 100)
    now = timezone.now()
    hostname = socket.gethostname()
    pid = os.getpid()

    # Step 1: Claim pending/failed events atomically
    with transaction.atomic():
        events = list(
            OutboxEvent.objects.select_for_update(skip_locked=True)
            .filter(
                status__in=[OutboxStatus.PENDING, OutboxStatus.FAILED]
            )
            .filter(
                Q(next_retry_at__lte=now) | Q(next_retry_at__isnull=True)
            )
            .order_by('aggregate_type', 'aggregate_id', 'sequence_number')[:batch_size]
        )

        if not events:
            return 0

        # Mark claimed events as PROCESSING
        for event in events:
            event.status = OutboxStatus.PROCESSING
            event.processing_started_at = now
            event.locked_at = now
            event.locked_by = f"{hostname}:{pid}"
            event.worker_hostname = hostname
            event.worker_pid = pid
            event.save(update_fields=[
                'status', 'processing_started_at', 'locked_at', 
                'locked_by', 'worker_hostname', 'worker_pid'
            ])

    processed_count = 0
    # Step 2: Publish each event outside of the lock transaction
    for event in events:
        try:
            # Publish event payload to broker (Celery task)
            dispatch_async_event.delay(event.event_name, event.payload)
            
            # Update success status
            event.status = OutboxStatus.PROCESSED
            event.published_to_broker_at = timezone.now()
            event.dispatched_at = timezone.now()
            event.processing_completed_at = timezone.now()
            event.locked_at = None
            event.locked_by = None
            event.save(update_fields=[
                'status', 'published_to_broker_at', 'dispatched_at', 
                'processing_completed_at', 'locked_at', 'locked_by'
            ])
            processed_count += 1
        except Exception as e:
            # Handle failure with exponential backoff and jitter
            event.dispatch_attempts += 1
            if event.dispatch_attempts >= 5:
                event.status = OutboxStatus.DEAD
            else:
                event.status = OutboxStatus.FAILED
                # Backoff: 2^attempts minutes + jitter (between -30s and 30s)
                jitter = random.uniform(-0.5, 0.5)
                backoff_minutes = max(0.1, (2 ** event.dispatch_attempts) + jitter)
                event.next_retry_at = timezone.now() + timedelta(minutes=backoff_minutes)
            
            event.last_error = str(e)
            event.locked_at = None
            event.locked_by = None
            event.save(update_fields=[
                'status', 'dispatch_attempts', 'next_retry_at', 
                'last_error', 'locked_at', 'locked_by'
            ])
            logger.error(f"Failed to publish outbox event {event.event_id}: {e}")

    return processed_count

@shared_task(name="core.recover_orphaned_locks")
def recover_orphaned_locks():
    """
    Recover events stuck in PROCESSING due to worker crashes.
    """
    lock_timeout_minutes = getattr(settings, 'OUTBOX_LOCK_TIMEOUT_MINUTES', 10)
    cutoff = timezone.now() - timedelta(minutes=lock_timeout_minutes)
    
    stuck_events = OutboxEvent.objects.filter(
        status=OutboxStatus.PROCESSING,
        locked_at__lt=cutoff
    )
    
    count = 0
    for event in stuck_events:
        event.status = OutboxStatus.FAILED
        event.locked_at = None
        event.locked_by = None
        event.last_error = "Lock timeout exceeded: worker crash assumed."
        event.save(update_fields=['status', 'locked_at', 'locked_by', 'last_error'])
        count += 1
        
    return count

@shared_task(name="core.archive_processed_outbox")
def archive_processed_outbox():
    """
    Archive/prune processed outbox events older than the retention threshold.
    """
    retention_days = getattr(settings, 'OUTBOX_RETENTION_DAYS', 30)
    cutoff = timezone.now() - timedelta(days=retention_days)
    
    old_events = OutboxEvent.objects.filter(
        status=OutboxStatus.PROCESSED,
        occurred_at__lt=cutoff
    )
    
    count = 0
    for event in old_events:
        event.status = OutboxStatus.ARCHIVED
        event.save(update_fields=['status'])
        count += 1
        
    return count

# Need to import Q dynamically if not imported
from django.db.models import Q


@shared_task(name="core.auto_clock_out_task")
def auto_clock_out_task(tenant_id, date_str):
    from backend.apps.hr.models.attendance import AttendanceRecord
    from backend.apps.hr.models.employee import EmployeeProfile
    from backend.apps.hr.services.attendance import AttendanceService
    from backend.apps.tenants.models import Tenant
    from datetime import datetime, time
    
    tenant = Tenant.objects.get(id=tenant_id)
    target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    
    # Process records missing check-out
    records = AttendanceRecord.objects.filter(
        tenant=tenant,
        attendance_date=target_date,
        check_in__isnull=False,
        check_out__isnull=True
    )
    
    for r in records:
        # Default auto clock-out time is shift end time, or 18:00
        out_time = r.shift.end_time if (r.shift and r.shift.end_time) else time(18, 0)
        out_dt = datetime.combine(target_date, out_time)
        # Call clock_out
        try:
            AttendanceService.clock_out(r.employee, out_dt, device_serial=None)
        except Exception as e:
            logger.error(f"Auto clock out failed for {r.employee.employee_number}: {e}")
            
    return records.count()


@shared_task(name="core.generate_daily_attendance_task")
def generate_daily_attendance_task(tenant_id, date_str):
    from backend.apps.tenants.models import Tenant
    from backend.apps.hr.services.attendance import AttendanceService
    from datetime import datetime
    
    tenant = Tenant.objects.get(id=tenant_id)
    target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    AttendanceService.generate_daily_attendance(tenant, target_date)
    return True


@shared_task(name="core.close_attendance_day_task")
def close_attendance_day_task(tenant_id, date_str):
    # Recalculates and locks daily attendance records
    from backend.apps.tenants.models import Tenant
    from backend.apps.hr.models.attendance import AttendanceRecord
    from backend.apps.hr.services.attendance import AttendanceService
    from datetime import datetime
    
    tenant = Tenant.objects.get(id=tenant_id)
    target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    
    records = AttendanceRecord.objects.filter(tenant=tenant, attendance_date=target_date)
    for r in records:
        AttendanceService.recalculate_attendance(tenant, r.employee, target_date, target_date)
        
    return records.count()


@shared_task(name="core.generate_attendance_summary_task")
def generate_attendance_summary_task(tenant_id, date_str):
    from backend.apps.tenants.models import Tenant
    from backend.apps.hr.models.attendance import AttendanceRecord, AttendanceSummary
    from django.db.models import Sum
    from decimal import Decimal
    from datetime import datetime
    
    tenant = Tenant.objects.get(id=tenant_id)
    target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    
    records = AttendanceRecord.objects.filter(tenant=tenant, attendance_date=target_date)
    
    present = records.filter(attendance_status='Present').count()
    late = records.filter(attendance_status='Late').count()
    absent = records.filter(attendance_status='Absent').count()
    leave = records.filter(attendance_status='Leave').count()
    overtime = records.aggregate(total_ot=Sum('overtime_hours'))['total_ot'] or Decimal('0.00')
    
    summary, created = AttendanceSummary.objects.get_or_create(
        tenant=tenant,
        date=target_date,
        defaults={
            'total_present': present,
            'total_late': late,
            'total_absent': absent,
            'total_leave': leave,
            'total_overtime_hours': overtime
        }
    )
    if not created:
        summary.total_present = present
        summary.total_late = late
        summary.total_absent = absent
        summary.total_leave = leave
        summary.total_overtime_hours = overtime
        summary.save()
        
    return str(summary.id)
