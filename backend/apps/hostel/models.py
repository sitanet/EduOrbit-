import uuid
from django.db import models
from django.utils import timezone
from backend.apps.core.models import TenantBaseModel, PlatformBaseModel

# ==============================================================
# RESIDENTIAL STRUCTURE
# ==============================================================

class Hostel(TenantBaseModel):
    """
    Hostel buildings / residential halls.
    """
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE)
    name = models.CharField(max_length=150)
    gender = models.CharField(max_length=10, default='mixed')  # male, female, mixed

    def __str__(self):
        return self.name


class HostelBlock(TenantBaseModel):
    hostel = models.ForeignKey(Hostel, on_delete=models.CASCADE, related_name='blocks')
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.hostel.name} - Block: {self.name}"


class HostelRoom(TenantBaseModel):
    block = models.ForeignKey(HostelBlock, on_delete=models.CASCADE, related_name='rooms')
    room_number = models.CharField(max_length=50)
    floor = models.CharField(max_length=50, blank=True)
    capacity = models.IntegerField(default=4)

    def __str__(self):
        return f"Room {self.room_number} ({self.block.name})"


class HostelBed(TenantBaseModel):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('occupied', 'Occupied'),
        ('maintenance', 'Maintenance')
    ]
    room = models.ForeignKey(HostelRoom, on_delete=models.CASCADE, related_name='beds')
    bed_number = models.CharField(max_length=50)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='available')

    def __str__(self):
        return f"{self.room.room_number} - Bed {self.bed_number}"


# ==============================================================
# BED ALLOCATIONS & ASSIGNMENTS
# ==============================================================

class HostelApplication(TenantBaseModel):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ]
    student = models.ForeignKey('people.Person', on_delete=models.CASCADE, related_name='hostel_applications')
    hostel = models.ForeignKey(Hostel, on_delete=models.CASCADE)
    application_date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"Hostel App for {self.student.person_number} ({self.status})"


class BedAllocation(TenantBaseModel):
    """
    Student residential assignments.
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed')
    ]
    bed = models.ForeignKey(HostelBed, on_delete=models.CASCADE, related_name='allocations')
    student = models.ForeignKey('people.Person', on_delete=models.CASCADE, related_name='hostel_allocations')
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='active')

    def __str__(self):
        return f"{self.student.person_number} allocated to Bed {self.bed.bed_number}"


# ==============================================================
# ROLL CALLS, VISITORS & INCIDENTS
# ==============================================================

class HostelRollCall(TenantBaseModel):
    """
    Nightly curfew roll-calls logs.
    """
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('excused', 'Excused')
    ]
    student = models.ForeignKey('people.Person', on_delete=models.CASCADE, related_name='hostel_rollcalls')
    date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='present')

    def __str__(self):
        return f"{self.student.person_number} on {self.date}: {self.status}"


class HostelVisitor(TenantBaseModel):
    visitor_name = models.CharField(max_length=150)
    purpose = models.CharField(max_length=150, blank=True)
    checked_in_at = models.DateTimeField(default=timezone.now)
    checked_out_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Visitor: {self.visitor_name} at {self.checked_in_at}"


class HostelIncident(TenantBaseModel):
    student = models.ForeignKey('people.Person', on_delete=models.CASCADE, related_name='hostel_incidents')
    title = models.CharField(max_length=150)
    description = models.TextField()
    incident_date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"Incident: {self.title} for {self.student.person_number}"


class RoomInspection(TenantBaseModel):
    room = models.ForeignKey(HostelRoom, on_delete=models.CASCADE, related_name='inspections')
    score = models.DecimalField(max_digits=5, decimal_places=2)
    inspection_date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"Inspection: {self.room.room_number} (Score: {self.score})"
