import uuid
from django.db import models
from django.utils import timezone
from backend.apps.core.models import TenantBaseModel

class AttendanceShift(TenantBaseModel):
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name="hr_attendance_shifts",
        db_index=True
    )
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=30)
    start_time = models.TimeField()
    end_time = models.TimeField()
    grace_minutes = models.IntegerField(default=0)
    break_start = models.TimeField(null=True, blank=True)
    break_end = models.TimeField(null=True, blank=True)
    minimum_hours = models.DecimalField(max_digits=4, decimal_places=2, default=0.00)
    overtime_after = models.DecimalField(max_digits=4, decimal_places=2, default=0.00)
    overnight_shift = models.BooleanField(default=False)
    version = models.IntegerField(default=1)
    active = models.BooleanField(default=True)
    
    # Geofencing Config
    allowed_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    allowed_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    allowed_radius_meters = models.IntegerField(null=True, blank=True)
    require_photo_verification = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.code}) V{self.version}"


class EmployeeAttendanceDevice(TenantBaseModel):
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name="hr_attendance_devices",
        db_index=True
    )
    device_name = models.CharField(max_length=100)
    device_type = models.CharField(max_length=50)  # Web, Mobile, Biometric, RFID, Facial Recognition, API
    serial_number = models.CharField(max_length=100, unique=True)
    api_key = models.CharField(max_length=255, db_index=True)
    location = models.CharField(max_length=150)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    active = models.BooleanField(default=True)
    last_seen = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.device_name} - {self.serial_number}"


class EmployeeShiftAssignment(TenantBaseModel):
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name="hr_shift_assignments",
        db_index=True
    )
    employee = models.ForeignKey('hr.EmployeeProfile', on_delete=models.CASCADE, related_name='shift_assignments')
    shift = models.ForeignKey(AttendanceShift, on_delete=models.CASCADE, related_name='employee_assignments')
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Shift Assignment: {self.employee.employee_number} -> {self.shift.name}"


class ShiftCalendar(TenantBaseModel):
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name="hr_shift_calendars",
        db_index=True
    )
    employee = models.ForeignKey('hr.EmployeeProfile', on_delete=models.CASCADE, related_name='shift_calendar_records')
    date = models.DateField()
    shift = models.ForeignKey(AttendanceShift, on_delete=models.CASCADE, related_name='shift_calendar_records')
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"ShiftCalendar: {self.employee.employee_number} on {self.date} -> {self.shift.name}"


class AttendanceLog(TenantBaseModel):
    """
    Raw check-in/out event log from biometric, RFID, mobile or web sources.
    """
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name="hr_attendance_logs",
        db_index=True
    )
    employee = models.ForeignKey('hr.EmployeeProfile', on_delete=models.CASCADE, related_name='attendance_logs')
    timestamp = models.DateTimeField()
    direction = models.CharField(max_length=10)  # IN, OUT
    source = models.CharField(max_length=50)  # Web, Mobile, Biometric, RFID, Facial Recognition, API
    device = models.ForeignKey(EmployeeAttendanceDevice, on_delete=models.SET_NULL, null=True, blank=True)
    gps_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    gps_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    photo_url = models.CharField(max_length=255, null=True, blank=True)
    face_match_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    raw_payload = models.JSONField(default=dict)
    verified = models.BooleanField(default=False)
    verification_error = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Raw Log: {self.employee.employee_number} - {self.direction} @ {self.timestamp}"


class AttendanceRecord(TenantBaseModel):
    """
    Processed working day metrics consumed by Payroll.
    """
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name="hr_attendance_records",
        db_index=True
    )
    employee = models.ForeignKey('hr.EmployeeProfile', on_delete=models.CASCADE, related_name='attendance_records')
    attendance_date = models.DateField()
    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)
    total_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    overtime_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    late_minutes = models.IntegerField(default=0)
    early_departure_minutes = models.IntegerField(default=0)
    attendance_status = models.CharField(max_length=30, default='Absent') # Present, Late, Absent, Half Day, Holiday, Weekend, Leave, Remote
    shift = models.ForeignKey(AttendanceShift, on_delete=models.SET_NULL, null=True, blank=True)
    shift_version = models.IntegerField(default=1)

    class Meta:
        unique_together = ('tenant', 'employee', 'attendance_date')

    def __str__(self):
        return f"AttendanceRecord: {self.employee.employee_number} on {self.attendance_date} ({self.attendance_status})"


class AttendanceAdjustment(TenantBaseModel):
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name="hr_attendance_adjustments",
        db_index=True
    )
    attendance_record = models.ForeignKey(AttendanceRecord, on_delete=models.CASCADE, related_name='adjustments')
    reason = models.TextField()
    requested_by = models.ForeignKey('hr.EmployeeProfile', on_delete=models.CASCADE, related_name='requested_adjustments')
    supervisor_approved_by = models.ForeignKey('hr.EmployeeProfile', on_delete=models.SET_NULL, null=True, blank=True, related_name='supervisor_approved_adjustments')
    supervisor_approved_at = models.DateTimeField(null=True, blank=True)
    hr_approved_by = models.ForeignKey('hr.EmployeeProfile', on_delete=models.SET_NULL, null=True, blank=True, related_name='hr_approved_adjustments')
    hr_approved_at = models.DateTimeField(null=True, blank=True)
    approval_status = models.CharField(max_length=30, default='Pending')  # Pending, Supervisor Approved, HR Approved, Rejected, Cancelled
    comments = models.TextField(blank=True)

    # Adjustment request details
    adjusted_check_in = models.TimeField(null=True, blank=True)
    adjusted_check_out = models.TimeField(null=True, blank=True)

    def __str__(self):
        return f"Adjustment: {self.attendance_record} ({self.approval_status})"


class AttendanceSummary(TenantBaseModel):
    """
    Daily aggregated values to speed up dashboard loads.
    """
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name="hr_attendance_summaries",
        db_index=True
    )
    date = models.DateField(unique=True)
    total_present = models.IntegerField(default=0)
    total_late = models.IntegerField(default=0)
    total_absent = models.IntegerField(default=0)
    total_leave = models.IntegerField(default=0)
    total_overtime_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Summary for {self.date}"
