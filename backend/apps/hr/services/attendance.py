import logging
from decimal import Decimal
from datetime import datetime, date, time, timedelta
from django.db import transaction
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.utils import timezone

from backend.apps.hr.models.employee import EmployeeProfile
from backend.apps.hr.models.leave import PublicHoliday, LeaveRequest
from backend.apps.hr.models.attendance import (
    AttendanceShift, EmployeeAttendanceDevice, EmployeeShiftAssignment,
    ShiftCalendar, AttendanceLog, AttendanceRecord, AttendanceAdjustment, AttendanceSummary
)
from backend.apps.hr.services.calculations import AttendanceCalculationEngineV1
from backend.apps.hr.validators.attendance import AttendanceValidator
from backend.apps.core.services.outbox import OutboxService

logger = logging.getLogger("eduorbit.attendance")

class AttendanceService:
    @staticmethod
    def get_active_shift(employee, target_date: date):
        # 1. Check ShiftCalendar rotation override first
        cal = ShiftCalendar.objects.filter(employee=employee, date=target_date, active=True).first()
        if cal:
            return cal.shift
            
        # 2. Fall back to EmployeeShiftAssignment ranges
        assign = EmployeeShiftAssignment.objects.filter(
            employee=employee,
            effective_from__lte=target_date
        ).filter(
            Q(effective_to__gte=target_date) | Q(effective_to__isnull=True)
        ).first()
        
        return assign.shift if assign else None

    @staticmethod
    @transaction.atomic
    def clock_in(employee, timestamp: datetime, device_serial=None, gps_lat=None, gps_lon=None, photo_url=None):
        tenant = employee.tenant
        target_date = timestamp.date()
        shift = AttendanceService.get_active_shift(employee, target_date)
        
        # Resolve device if provided
        device = None
        if device_serial:
            device = EmployeeAttendanceDevice.objects.filter(tenant=tenant, serial_number=device_serial, active=True).first()

        # Validate clock-in
        verified = True
        error_msg = ""
        try:
            AttendanceValidator.validate_clock_in(employee, timestamp, gps_lat, gps_lon, shift)
        except ValidationError as e:
            verified = False
            error_msg = str(e.message if hasattr(e, 'message') else e)
            logger.warning(f"Geofence/Clock-in validation failed for {employee.employee_number}: {error_msg}")
            # If photo verification failed or geofence violated, we raise validation error to user
            # but write raw event as unverified
            AttendanceLog.objects.create(
                tenant=tenant,
                employee=employee,
                timestamp=timestamp,
                direction='IN',
                source='Mobile' if gps_lat else 'Web',
                device=device,
                gps_latitude=gps_lat,
                gps_longitude=gps_lon,
                photo_url=photo_url,
                verified=False,
                verification_error=error_msg
            )
            raise e

        # Write Raw Log
        log = AttendanceLog.objects.create(
            tenant=tenant,
            employee=employee,
            timestamp=timestamp,
            direction='IN',
            source=device.device_type if device else ('Mobile' if gps_lat else 'Web'),
            device=device,
            gps_latitude=gps_lat,
            gps_longitude=gps_lon,
            photo_url=photo_url,
            verified=True
        )

        # Get or create processed Record
        record, created = AttendanceRecord.objects.get_or_create(
            tenant=tenant,
            employee=employee,
            attendance_date=target_date,
            defaults={
                'shift': shift,
                'shift_version': shift.version if shift else 1,
                'attendance_status': 'Absent'
            }
        )

        record.check_in = timestamp.time()
        record.shift = shift
        record.shift_version = shift.version if shift else 1
        
        # Calculate if check-out already exists
        if record.check_out:
            in_dt = datetime.combine(target_date, record.check_in)
            out_dt = datetime.combine(target_date, record.check_out)
            if shift and shift.overnight_shift and record.check_out < record.check_in:
                out_dt += timedelta(days=1)
                
            # Check leave/holiday context
            is_holiday = PublicHoliday.objects.filter(tenant=tenant, date=target_date, active=True).exists()
            is_weekend = target_date.weekday() in [5, 6]
            is_leave = LeaveRequest.objects.filter(employee=employee, start_date__lte=target_date, end_date__gte=target_date, status='approved').exists()

            res = AttendanceCalculationEngineV1.calculate(
                check_in_dt=in_dt,
                check_out_dt=out_dt,
                shift=shift,
                is_holiday=is_holiday,
                is_weekend=is_weekend,
                is_leave=is_leave
            )
            record.total_hours = res.total_hours
            record.overtime_hours = res.overtime_hours
            record.late_minutes = res.late_minutes
            record.early_departure_minutes = res.early_departure_minutes
            record.attendance_status = res.attendance_status
        else:
            # Mark status based on lateness threshold immediately
            if shift:
                shift_start = timezone.make_aware(datetime.combine(target_date, shift.start_time)) if timezone.is_aware(timestamp) else datetime.combine(target_date, shift.start_time)
                diff_min = int((timestamp - shift_start).total_seconds() // 60)
                if diff_min > shift.grace_minutes:
                    record.attendance_status = 'Late'
                    record.late_minutes = diff_min
                else:
                    record.attendance_status = 'Present'

        record.save()

        # Publish Outbox Event
        OutboxService.record_event(
            tenant=tenant,
            event_name="attendance.clocked_in",
            aggregate_type="AttendanceRecord",
            aggregate_id=str(record.id),
            payload={
                "employee_id": str(employee.id),
                "timestamp": timestamp.isoformat(),
                "direction": "IN",
                "status": record.attendance_status
            }
        )
        return record

    @staticmethod
    @transaction.atomic
    def clock_out(employee, timestamp: datetime, device_serial=None, gps_lat=None, gps_lon=None, photo_url=None):
        tenant = employee.tenant
        target_date = timestamp.date()
        shift = AttendanceService.get_active_shift(employee, target_date)
        
        device = None
        if device_serial:
            device = EmployeeAttendanceDevice.objects.filter(tenant=tenant, serial_number=device_serial, active=True).first()

        # Validate clock-out
        try:
            AttendanceValidator.validate_clock_out(employee, timestamp)
        except ValidationError as e:
            AttendanceLog.objects.create(
                tenant=tenant,
                employee=employee,
                timestamp=timestamp,
                direction='OUT',
                source='Mobile' if gps_lat else 'Web',
                device=device,
                gps_latitude=gps_lat,
                gps_longitude=gps_lon,
                photo_url=photo_url,
                verified=False,
                verification_error=str(e)
            )
            raise e

        # Write Raw Log
        log = AttendanceLog.objects.create(
            tenant=tenant,
            employee=employee,
            timestamp=timestamp,
            direction='OUT',
            source=device.device_type if device else ('Mobile' if gps_lat else 'Web'),
            device=device,
            gps_latitude=gps_lat,
            gps_longitude=gps_lon,
            photo_url=photo_url,
            verified=True
        )

        record, created = AttendanceRecord.objects.get_or_create(
            tenant=tenant,
            employee=employee,
            attendance_date=target_date,
            defaults={
                'shift': shift,
                'shift_version': shift.version if shift else 1,
                'attendance_status': 'Absent'
            }
        )

        record.check_out = timestamp.time()
        record.shift = shift
        record.shift_version = shift.version if shift else 1

        # Calculate metrics if check-in exists
        if record.check_in:
            in_dt = datetime.combine(target_date, record.check_in)
            out_dt = datetime.combine(target_date, record.check_out)
            if shift and shift.overnight_shift and record.check_out < record.check_in:
                out_dt += timedelta(days=1)
                
            is_holiday = PublicHoliday.objects.filter(tenant=tenant, date=target_date, active=True).exists()
            is_weekend = target_date.weekday() in [5, 6]
            is_leave = LeaveRequest.objects.filter(employee=employee, start_date__lte=target_date, end_date__gte=target_date, status='approved').exists()

            res = AttendanceCalculationEngineV1.calculate(
                check_in_dt=in_dt,
                check_out_dt=out_dt,
                shift=shift,
                is_holiday=is_holiday,
                is_weekend=is_weekend,
                is_leave=is_leave
            )
            record.total_hours = res.total_hours
            record.overtime_hours = res.overtime_hours
            record.late_minutes = res.late_minutes
            record.early_departure_minutes = res.early_departure_minutes
            record.attendance_status = res.attendance_status
        else:
            record.attendance_status = 'Absent'

        record.save()

        # Publish Event
        OutboxService.record_event(
            tenant=tenant,
            event_name="attendance.clocked_out",
            aggregate_type="AttendanceRecord",
            aggregate_id=str(record.id),
            payload={
                "employee_id": str(employee.id),
                "timestamp": timestamp.isoformat(),
                "direction": "OUT",
                "status": record.attendance_status
            }
        )
        return record

    @staticmethod
    @transaction.atomic
    def generate_daily_attendance(tenant, target_date: date):
        """
        Creates default attendance records (Absent/Weekend/Holiday/Leave) 
        for all active employees who did not check in.
        Runs in high-performance chunks of 500.
        """
        employees = EmployeeProfile.objects.filter(tenant=tenant, is_deleted=False)
        
        # Find which employees already have a record for today
        existing_emp_ids = AttendanceRecord.objects.filter(
            tenant=tenant,
            attendance_date=target_date
        ).values_list('employee_id', flat=True)

        missing_employees = employees.exclude(id__in=existing_emp_ids)
        
        is_holiday = PublicHoliday.objects.filter(tenant=tenant, date=target_date, active=True).exists()
        is_weekend = target_date.weekday() in [5, 6]
        
        records_to_create = []
        chunk_size = 500
        
        for emp in missing_employees:
            shift = AttendanceService.get_active_shift(emp, target_date)
            is_leave = LeaveRequest.objects.filter(employee=emp, start_date__lte=target_date, end_date__gte=target_date, status='approved').exists()

            # Pure stateless default status check
            res = AttendanceCalculationEngineV1.calculate(
                check_in_dt=None,
                shift=shift,
                is_holiday=is_holiday,
                is_weekend=is_weekend,
                is_leave=is_leave
            )
            
            records_to_create.append(
                AttendanceRecord(
                    tenant=tenant,
                    employee=emp,
                    attendance_date=target_date,
                    shift=shift,
                    shift_version=shift.version if shift else 1,
                    attendance_status=res.attendance_status,
                    total_hours=Decimal('0.00'),
                    overtime_hours=Decimal('0.00')
                )
            )
            
            # Bulk create in chunks
            if len(records_to_create) >= chunk_size:
                AttendanceRecord.objects.bulk_create(records_to_create)
                records_to_create = []

        if records_to_create:
            AttendanceRecord.objects.bulk_create(records_to_create)

        # Trigger domain events
        OutboxService.record_event(
            tenant=tenant,
            event_name="attendance.generated",
            aggregate_type="AttendanceSummary",
            aggregate_id=str(target_date),
            payload={
                "date": target_date.isoformat(),
                "generated_count": missing_employees.count()
            }
        )

    @staticmethod
    @transaction.atomic
    def approve_adjustment(tenant, adjustment_id, supervisor=None, hr=None, action='approve'):
        adj = AttendanceAdjustment.objects.select_for_update().get(id=adjustment_id, tenant=tenant)
        
        if action == 'reject':
            adj.approval_status = 'Rejected'
            adj.save()
            return adj
        elif action == 'cancel':
            adj.approval_status = 'Cancelled'
            adj.save()
            return adj

        if supervisor and adj.approval_status == 'Pending':
            adj.supervisor_approved_by = supervisor
            adj.supervisor_approved_at = timezone.now()
            adj.approval_status = 'Supervisor Approved'
            adj.save()
            
        elif hr and adj.approval_status == 'Supervisor Approved':
            adj.hr_approved_by = hr
            adj.hr_approved_at = timezone.now()
            adj.approval_status = 'HR Approved'
            adj.save()

            # Apply adjustment updates to processed record
            record = adj.attendance_record
            if adj.adjusted_check_in:
                record.check_in = adj.adjusted_check_in
            if adj.adjusted_check_out:
                record.check_out = adj.adjusted_check_out
            
            # Recalculate record metrics
            shift = record.shift
            target_date = record.attendance_date
            
            if record.check_in and record.check_out:
                in_dt = datetime.combine(target_date, record.check_in)
                out_dt = datetime.combine(target_date, record.check_out)
                if shift and shift.overnight_shift and record.check_out < record.check_in:
                    out_dt += timedelta(days=1)

                is_holiday = PublicHoliday.objects.filter(tenant=tenant, date=target_date, active=True).exists()
                is_weekend = target_date.weekday() in [5, 6]
                is_leave = LeaveRequest.objects.filter(employee=record.employee, start_date__lte=target_date, end_date__gte=target_date, status='approved').exists()

                res = AttendanceCalculationEngineV1.calculate(
                    check_in_dt=in_dt,
                    check_out_dt=out_dt,
                    shift=shift,
                    is_holiday=is_holiday,
                    is_weekend=is_weekend,
                    is_leave=is_leave
                )
                record.total_hours = res.total_hours
                record.overtime_hours = res.overtime_hours
                record.late_minutes = res.late_minutes
                record.early_departure_minutes = res.early_departure_minutes
                record.attendance_status = res.attendance_status
                record.save()

        # Publish outbox log
        OutboxService.record_event(
            tenant=tenant,
            event_name="attendance.adjusted",
            aggregate_type="AttendanceAdjustment",
            aggregate_id=str(adj.id),
            payload={
                "record_id": str(adj.attendance_record.id),
                "status": adj.approval_status
            }
        )
        return adj

    @staticmethod
    @transaction.atomic
    def recalculate_attendance(tenant, employee, start_date: date, end_date: date):
        records = AttendanceRecord.objects.select_for_update().filter(
            employee=employee,
            attendance_date__range=(start_date, end_date)
        )
        
        for record in records:
            shift = record.shift or AttendanceService.get_active_shift(employee, record.attendance_date)
            target_date = record.attendance_date
            
            if record.check_in and record.check_out:
                in_dt = datetime.combine(target_date, record.check_in)
                out_dt = datetime.combine(target_date, record.check_out)
                if shift and shift.overnight_shift and record.check_out < record.check_in:
                    out_dt += timedelta(days=1)
                    
                is_holiday = PublicHoliday.objects.filter(tenant=tenant, date=target_date, active=True).exists()
                is_weekend = target_date.weekday() in [5, 6]
                is_leave = LeaveRequest.objects.filter(employee=employee, start_date__lte=target_date, end_date__gte=target_date, status='approved').exists()

                res = AttendanceCalculationEngineV1.calculate(
                    check_in_dt=in_dt,
                    check_out_dt=out_dt,
                    shift=shift,
                    is_holiday=is_holiday,
                    is_weekend=is_weekend,
                    is_leave=is_leave
                )
                record.total_hours = res.total_hours
                record.overtime_hours = res.overtime_hours
                record.late_minutes = res.late_minutes
                record.early_departure_minutes = res.early_departure_minutes
                record.attendance_status = res.attendance_status
                record.shift = shift
                record.shift_version = shift.version if shift else 1
                record.save()

        OutboxService.record_event(
            tenant=tenant,
            event_name="attendance.recalculated",
            aggregate_type="EmployeeProfile",
            aggregate_id=str(employee.id),
            payload={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        )
