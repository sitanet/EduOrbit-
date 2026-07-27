from django.db import transaction
from django.utils import timezone
from backend.apps.attendance.models import (
    AttendanceSession, AttendanceRecord, AttendanceStatus, AttendanceSource, AttendanceReason
)
from backend.apps.core.services.notifications import UnifiedNotificationService

class AttendanceService:
    """
    Academic & Core Attendance Management Service.
    Handles Single Check-in/Check-out, Bulk Marking, Corrections, and Absentees Notification.
    """
    @classmethod
    @transaction.atomic
    def mark_attendance(cls, session, person, status_code='present', source_code='manual', reason_code=None):
        tenant = session.tenant

        # 1. Get or create status & source
        status_obj, _ = AttendanceStatus.objects.get_or_create(code=status_code, defaults={'name': status_code.capitalize()})
        source_obj, _ = AttendanceSource.objects.get_or_create(code=source_code, defaults={'name': source_code.upper()})
        
        reason_obj = None
        if reason_code:
            reason_obj, _ = AttendanceReason.objects.get_or_create(code=reason_code, defaults={'name': reason_code.capitalize()})

        # 2. Update or create AttendanceRecord
        record, created = AttendanceRecord.objects.update_or_create(
            session=session,
            person=person,
            tenant=tenant,
            defaults={
                'status': status_obj,
                'source': source_obj,
                'reason': reason_obj,
                'time_marked': timezone.now()
            }
        )

        # 3. Absent / Late Notification Dispatch
        if status_code in ['absent', 'late']:
            UnifiedNotificationService.send_notification(
                recipient=person.first_name,
                title=f"Attendance Alert: Marked {status_code.upper()}",
                message=f"{person.first_name} {person.last_name} was marked {status_code} on {session.date}.",
                channels=['in_app', 'email', 'sms']
            )

        return {
            "status": "success",
            "record_id": str(record.id),
            "person": f"{person.first_name} {person.last_name}",
            "attendance_status": status_code,
            "created": created
        }

    @classmethod
    @transaction.atomic
    def bulk_mark_attendance(cls, session, records_data):
        results = []
        for item in records_data:
            res = cls.mark_attendance(
                session=session,
                person=item['person'],
                status_code=item.get('status_code', 'present'),
                source_code=item.get('source_code', 'manual'),
                reason_code=item.get('reason_code')
            )
            results.append(res)

        return {
            "status": "success",
            "marked_count": len(results),
            "session_id": str(session.id)
        }

    @classmethod
    def get_attendance_summary(cls, person):
        records = AttendanceRecord.objects.filter(person=person).select_related('status')
        total = records.count()
        present_count = records.filter(status__code='present').count()
        late_count = records.filter(status__code='late').count()
        absent_count = records.filter(status__code='absent').count()

        percentage = ((present_count + late_count) / total * 100.0) if total > 0 else 100.00

        return {
            "person": f"{person.first_name} {person.last_name}",
            "total_sessions": total,
            "present_count": present_count,
            "late_count": late_count,
            "absent_count": absent_count,
            "attendance_percentage": round(percentage, 2)
        }
