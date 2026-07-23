import uuid
from django.db import models
from django.utils import timezone
from backend.apps.core.models import TenantBaseModel, PlatformBaseModel

# ==============================================================
# FACILITIES & PHYSICAL LAYOUTS
# ==============================================================

class Building(TenantBaseModel):
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE)
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=50)
    gps_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    gps_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    def __str__(self):
        return self.name


class Floor(TenantBaseModel):
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='floors')
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.building.name} - {self.name}"


class Room(TenantBaseModel):
    floor = models.ForeignKey(Floor, on_delete=models.CASCADE, related_name='rooms')
    room_number = models.CharField(max_length=50)
    room_type = models.CharField(max_length=100)  # classroom, laboratory, office

    def __str__(self):
        return f"Room {self.room_number} ({self.floor})"


class Facility(TenantBaseModel):
    """
    Physical facility items (AC, solar panels, water pumps, projectors).
    """
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='facilities')
    name = models.CharField(max_length=150)
    category = models.CharField(max_length=100)  # HVAC, generator, utility

    def __str__(self):
        return f"{self.name} in {self.room.room_number}"


# ==============================================================
# WORK ORDER ENGINE
# ==============================================================

class WorkRequest(TenantBaseModel):
    requester = models.ForeignKey('people.Person', on_delete=models.CASCADE, related_name='work_requests')
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    description = models.TextField()
    priority = models.CharField(max_length=30, default='medium')  # low, medium, high

    def __str__(self):
        return f"Request for {self.room.room_number} ({self.priority})"


class WorkOrder(TenantBaseModel):
    STATUS_CHOICES = [
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('verified', 'Verified'),
        ('closed', 'Closed')
    ]
    request = models.ForeignKey(WorkRequest, on_delete=models.CASCADE, related_name='orders')
    assigned_to = models.ForeignKey('people.Person', on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='assigned')
    actual_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"WO {self.id}: {self.status}"


class WorkLog(TenantBaseModel):
    order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name='logs')
    action = models.CharField(max_length=100)
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.action} at {self.timestamp}"


# ==============================================================
# MAINTENANCE, INSPECTIONS & UTILITIES
# ==============================================================

class FacilityMaintenancePlan(TenantBaseModel):
    name = models.CharField(max_length=150)
    recurrence = models.CharField(max_length=50)  # daily, weekly, monthly

    def __str__(self):
        return self.name


class FacilityMaintenanceSchedule(TenantBaseModel):
    plan = models.ForeignKey(FacilityMaintenancePlan, on_delete=models.CASCADE, related_name='schedules')
    next_due_date = models.DateField()

    def __str__(self):
        return f"{self.plan.name} due on {self.next_due_date}"


class Inspection(TenantBaseModel):
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='inspections')
    inspector = models.ForeignKey('people.Person', on_delete=models.CASCADE)
    score = models.DecimalField(max_digits=5, decimal_places=2)
    inspection_date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"Inspection: {self.building.name} Score: {self.score}"


class UtilityMeter(TenantBaseModel):
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='meters')
    meter_type = models.CharField(max_length=50)  # electricity, water, gas

    def __str__(self):
        return f"{self.meter_type} meter - {self.building.name}"


class UtilityReading(TenantBaseModel):
    meter = models.ForeignKey(UtilityMeter, on_delete=models.CASCADE, related_name='readings')
    reading_value = models.DecimalField(max_digits=12, decimal_places=2)
    reading_date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"{self.meter.meter_type}: {self.reading_value} on {self.reading_date}"
