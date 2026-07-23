import uuid
from django.db import models
from django.utils import timezone
from backend.apps.core.models import TenantBaseModel, PlatformBaseModel

# ==============================================================
# POLICIES, SOURCES, AND BIOMETRIC DEVICES
# ==============================================================

class AttendancePolicy(TenantBaseModel):
    """
    School-specific rules regulating attendance expectations (e.g. grace periods).
    """
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE, related_name='attendance_policies')
    min_attendance_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=75.00)
    late_grace_period_minutes = models.IntegerField(default=15)
    auto_mark_absent_minutes = models.IntegerField(default=30)

    def __str__(self):
        return f"Policy for {self.school.name}"


class AttendanceSource(PlatformBaseModel):
    """
    Capture channels (Manual registration, QR scans, Biometric gates, GPS check-ins).
    """
    name = models.CharField(max_length=100)  # e.g., QR Code Scan
    code = models.CharField(max_length=50, unique=True)  # e.g., 'qr'

    def __str__(self):
        return self.name


class AttendanceDevice(TenantBaseModel):
    """
    IoT card readers or facial terminals registered in the school building.
    """
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE)
    device_identifier = models.CharField(max_length=100, unique=True)
    device_type = models.CharField(max_length=50)  # facial_terminal, rfid_reader
    location = models.CharField(max_length=150)
    status = models.CharField(max_length=30, default='active')
    last_sync = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.device_identifier} ({self.location})"


# ==============================================================
# SESSIONS, RECORDS, & STATUS LOOKUPS
# ==============================================================

class AttendanceReason(PlatformBaseModel):
    name = models.CharField(max_length=100)  # e.g. Sick Leave
    code = models.CharField(max_length=50, unique=True)  # e.g. 'sick'

    def __str__(self):
        return self.name


class AttendanceType(PlatformBaseModel):
    name = models.CharField(max_length=100)  # e.g., Lesson Attendance
    code = models.CharField(max_length=50, unique=True)  # e.g., 'lesson'

    def __str__(self):
        return self.name


class AttendanceStatus(PlatformBaseModel):
    name = models.CharField(max_length=100)  # Present, Absent, Late
    code = models.CharField(max_length=50, unique=True)  # e.g., 'present'

    def __str__(self):
        return self.name


class AttendanceSession(TenantBaseModel):
    """
    Represents the session context (e.g. Tuesday Science lesson).
    """
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE)
    attendance_type = models.ForeignKey(AttendanceType, on_delete=models.CASCADE)
    lesson_instance = models.ForeignKey('teachers.LessonInstance', on_delete=models.CASCADE, null=True, blank=True)
    date = models.DateField(default=timezone.now)

    def __str__(self):
        if self.lesson_instance:
            return f"Session: {self.lesson_instance} ({self.date})"
        return f"Daily roll call ({self.date})"


class AttendanceRecord(TenantBaseModel):
    """
    The actual attendance log mapping a unified Person profile to a status.
    """
    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name='records')
    person = models.ForeignKey('people.Person', on_delete=models.CASCADE, related_name='attendance_records')
    status = models.ForeignKey(AttendanceStatus, on_delete=models.CASCADE)
    source = models.ForeignKey(AttendanceSource, on_delete=models.CASCADE)
    
    reason = models.ForeignKey(AttendanceReason, on_delete=models.SET_NULL, null=True, blank=True)
    device = models.ForeignKey(AttendanceDevice, on_delete=models.SET_NULL, null=True, blank=True)
    time_marked = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.person.last_name} -> {self.status.name} ({self.time_marked})"


# ==============================================================
# CORRECTIONS, EARLY PICKUPS, & OFFLINE QUEUES
# ==============================================================

class AttendanceCorrection(TenantBaseModel):
    """
    Formal requests to alter historical logs.
    """
    record = models.ForeignKey(AttendanceRecord, on_delete=models.CASCADE, related_name='corrections')
    requested_status = models.ForeignKey(AttendanceStatus, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, default='pending')  # pending, approved, rejected
    reason = models.TextField()
    requested_by_user_id = models.UUIDField()

    def __str__(self):
        return f"Correction for {self.record.person.last_name} ({self.status})"


class ParentPickup(TenantBaseModel):
    """
    Pickup logs for early childhood education (ECE) verification.
    """
    student = models.ForeignKey('people.StudentProfile', on_delete=models.CASCADE)
    authorized_person = models.ForeignKey('people.Person', on_delete=models.CASCADE)
    pickup_time = models.DateTimeField(default=timezone.now)
    verification_method = models.CharField(max_length=30, default='pin')  # pin, qr

    def __str__(self):
        return f"Pickup of {self.student.student_number} by {self.authorized_person.last_name}"


class OfflineSyncQueue(TenantBaseModel):
    """
    Storage payload staging offline check-in sync actions.
    """
    client_uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    device = models.ForeignKey(AttendanceDevice, on_delete=models.SET_NULL, null=True, blank=True)
    payload = models.JSONField(default=dict)
    sync_status = models.CharField(max_length=20, default='pending')  # pending, success, conflict
    local_timestamp = models.DateTimeField()
    server_timestamp = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Sync log #{self.client_uuid} ({self.sync_status})"


class AttendanceAnalytics(TenantBaseModel):
    """
    Summaries caching chronic absenteeism indices.
    """
    academic_year = models.ForeignKey('academic.AcademicYear', on_delete=models.CASCADE)
    class_record = models.ForeignKey('academic.AcademicClass', on_delete=models.CASCADE, null=True, blank=True)
    attendance_rate = models.DecimalField(max_digits=5, decimal_places=2)
    calculation_date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"Rate: {self.attendance_rate}% on {self.calculation_date}"
