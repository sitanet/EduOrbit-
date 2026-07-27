from decimal import Decimal
from dataclasses import dataclass
from datetime import datetime, date, time, timedelta

@dataclass(frozen=True)
class AttendanceResult:
    total_hours: Decimal
    overtime_hours: Decimal
    late_minutes: int
    early_departure_minutes: int
    attendance_status: str  # Present, Late, Absent, Half Day, Holiday, Weekend, Leave, Remote
    night_shift_hours: Decimal = Decimal('0.00')

class AttendanceCalculationEngineV1:
    @staticmethod
    def calculate(check_in_dt: datetime = None, check_out_dt: datetime = None, 
                  shift = None, is_holiday: bool = False, is_weekend: bool = False, 
                  is_leave: bool = False, is_remote: bool = False) -> AttendanceResult:
        """
        Pure, stateless engine for calculating employee attendance metrics.
        All datetime inputs are expected to be timezone-aware or matching timezone contexts.
        """
        # 1. Leave overlap takes highest precedence
        if is_leave:
            return AttendanceResult(
                total_hours=Decimal('0.00'),
                overtime_hours=Decimal('0.00'),
                late_minutes=0,
                early_departure_minutes=0,
                attendance_status='Leave'
            )

        # 2. If no check-in occurred, check holiday/weekend default status
        if not check_in_dt:
            status = 'Absent'
            if is_holiday:
                status = 'Holiday'
            elif is_weekend:
                status = 'Weekend'
            
            return AttendanceResult(
                total_hours=Decimal('0.00'),
                overtime_hours=Decimal('0.00'),
                late_minutes=0,
                early_departure_minutes=0,
                attendance_status=status
            )

        # 3. Check-in exists, but missing check-out: Incomplete log -> default to Absent/Half Day
        if not check_out_dt:
            # Missing check-out is flagged as Absent in normal flow until adjusted/recalculated
            return AttendanceResult(
                total_hours=Decimal('0.00'),
                overtime_hours=Decimal('0.00'),
                late_minutes=0,
                early_departure_minutes=0,
                attendance_status='Absent'
            )

        # 4. We have both check-in and check-out
        # Compute raw difference in hours
        duration = check_out_dt - check_in_dt
        duration_seconds = duration.total_seconds()
        
        # Handle cross-midnight overnight shift
        if duration_seconds < 0 and shift and shift.overnight_shift:
            # Add 24 hours
            duration_seconds += 86400
            
        total_hours = Decimal(str(max(0.0, duration_seconds / 3600.0))).quantize(Decimal('0.01'))

        # Deduct break time if shift and check-in/out overlaps with break window
        if shift and shift.break_start and shift.break_end:
            # Convert break times to datetime on target date to subtract correctly
            # To simplify, we assume break is a standard duration
            b_start_dt = datetime.combine(check_in_dt.date(), shift.break_start)
            b_end_dt = datetime.combine(check_in_dt.date(), shift.break_end)
            if b_end_dt < b_start_dt: # Overnight break
                b_end_dt += timedelta(days=1)
                
            # If check_in is before break start and check_out is after break end
            if check_in_dt <= b_start_dt and check_out_dt >= b_end_dt:
                break_duration = (b_end_dt - b_start_dt).total_seconds() / 3600.0
                total_hours = max(Decimal('0.00'), total_hours - Decimal(str(break_duration))).quantize(Decimal('0.01'))

        # Compute lateness
        late_minutes = 0
        if shift and shift.start_time:
            # Combine to datetime for matching date
            shift_start_dt = datetime.combine(check_in_dt.date(), shift.start_time)
            
            # Handle check_in compared to shift start
            # If check-in is after shift start time
            if check_in_dt > shift_start_dt:
                diff_sec = (check_in_dt - shift_start_dt).total_seconds()
                diff_min = int(diff_sec // 60)
                if diff_min > shift.grace_minutes:
                    late_minutes = diff_min

        # Compute early departure
        early_departure_minutes = 0
        if shift and shift.end_time:
            shift_end_dt = datetime.combine(check_in_dt.date(), shift.end_time)
            if shift.overnight_shift and shift.end_time < shift.start_time:
                shift_end_dt += timedelta(days=1)
                
            if check_out_dt < shift_end_dt:
                diff_sec = (shift_end_dt - check_out_dt).total_seconds()
                early_departure_minutes = int(diff_sec // 60)

        # Compute night shift hours (e.g. hours worked between 10 PM and 6 AM)
        night_shift_hours = Decimal('0.00')
        # We can calculate simple overnight hours if overnight_shift is enabled
        if shift and shift.overnight_shift:
            # Let's count hours worked after 22:00 (10 PM) or before 06:00 (6 AM)
            # For simplicity, count total hours as night shift hours if it's marked overnight
            night_shift_hours = total_hours

        # Compute overtime
        overtime_hours = Decimal('0.00')
        if shift and shift.overtime_after > 0:
            if total_hours > shift.overtime_after:
                overtime_hours = (total_hours - shift.overtime_after).quantize(Decimal('0.01'))

        # Determine attendance status
        if is_holiday:
            status = 'Holiday'
        elif is_weekend:
            status = 'Weekend'
        elif is_remote:
            status = 'Remote'
        else:
            if shift and total_hours < shift.minimum_hours:
                status = 'Half Day'
            elif late_minutes > 0:
                status = 'Late'
            else:
                status = 'Present'

        return AttendanceResult(
            total_hours=total_hours,
            overtime_hours=overtime_hours,
            late_minutes=late_minutes,
            early_departure_minutes=early_departure_minutes,
            attendance_status=status,
            night_shift_hours=night_shift_hours
        )
