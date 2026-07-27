import math
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, date
from backend.apps.hr.models.attendance import (
    AttendanceRecord, AttendanceShift, EmployeeShiftAssignment, AttendanceLog, ShiftCalendar
)

class AttendanceValidator:
    @staticmethod
    def validate_clock_in(employee, timestamp: datetime, gps_lat=None, gps_lon=None, shift=None):
        if timestamp > timezone.now():
            raise ValidationError("Cannot clock in for a future date/time.")

        # Duplicate/Replay prevention: check if another check-in exists within 1 minute
        recent_log = AttendanceLog.objects.filter(
            employee=employee,
            direction='IN',
            timestamp__range=(timestamp - timezone.timedelta(minutes=1), timestamp + timezone.timedelta(minutes=1))
        ).exists()
        if recent_log:
            raise ValidationError("Duplicate clock-in log detected within 1 minute threshold.")

        # Geofence validation
        if shift and shift.allowed_latitude and shift.allowed_longitude and shift.allowed_radius_meters:
            if gps_lat is None or gps_lon is None:
                raise ValidationError("GPS coordinates are required for geofenced shift check-in.")
            
            # Compute distance in meters using Haversine formula
            distance = AttendanceValidator._calculate_distance(
                float(shift.allowed_latitude), float(shift.allowed_longitude),
                float(gps_lat), float(gps_lon)
            )
            if distance > float(shift.allowed_radius_meters):
                raise ValidationError(f"Clock-in location is outside the allowed radius. Distance: {distance:.2f} meters.")

    @staticmethod
    def validate_clock_out(employee, timestamp: datetime):
        if timestamp > timezone.now():
            raise ValidationError("Cannot clock out for a future date/time.")
            
        recent_log = AttendanceLog.objects.filter(
            employee=employee,
            direction='OUT',
            timestamp__range=(timestamp - timezone.timedelta(minutes=1), timestamp + timezone.timedelta(minutes=1))
        ).exists()
        if recent_log:
            raise ValidationError("Duplicate clock-out log detected within 1 minute threshold.")

    @staticmethod
    def validate_shift_assignment(employee, shift, effective_from: date, effective_to: date = None):
        # Prevent overlapping shift assignments for the same employee
        qs = EmployeeShiftAssignment.objects.filter(employee=employee)
        for assign in qs:
            # Overlap logic
            start_a = assign.effective_from
            end_a = assign.effective_to or date(9999, 12, 31)
            
            start_b = effective_from
            end_b = effective_to or date(9999, 12, 31)
            
            if start_a <= end_b and start_b <= end_a:
                raise ValidationError(f"Overlapping shift assignment found with shift {assign.shift.name} starting {assign.effective_from}.")

    @staticmethod
    def _calculate_distance(lat1, lon1, lat2, lon2):
        """
        Haversine formula to compute distance in meters between two coordinates.
        """
        R = 6371000.0  # Earth radius in meters
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        
        a = (math.sin(dphi / 2.0) ** 2 +
             math.cos(phi1) * math.cos(phi2) *
             math.sin(dlambda / 2.0) ** 2)
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return R * c
