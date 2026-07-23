import uuid
from django.db import models
from django.utils import timezone
from backend.apps.core.models import TenantBaseModel, PlatformBaseModel

# ==============================================================
# FLEET MANAGEMENT & DRIVERS
# ==============================================================

class VehicleCategory(TenantBaseModel):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Vehicle(TenantBaseModel):
    """
    Physical vehicle fleet inventory assets.
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('maintenance', 'In Maintenance'),
        ('retired', 'Retired')
    ]
    category = models.ForeignKey(VehicleCategory, on_delete=models.SET_NULL, null=True, blank=True)
    registration_number = models.CharField(max_length=100, unique=True)
    plate_number = models.CharField(max_length=50)
    capacity = models.IntegerField(default=30)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='active')

    def __str__(self):
        return f"{self.registration_number} ({self.plate_number})"


class Driver(TenantBaseModel):
    """
    Extends base Person table with driver licensing and status mappings.
    """
    person = models.OneToOneField('people.Person', on_delete=models.CASCADE, related_name='driver_profile')
    license_number = models.CharField(max_length=100)
    status = models.CharField(max_length=30, default='active')

    def __str__(self):
        return f"Driver: {self.person.first_name} {self.person.last_name}"


# ==============================================================
# ROUTES, STOPS & TRIP SCHEDULES
# ==============================================================

class Route(TenantBaseModel):
    name = models.CharField(max_length=150)
    start_point = models.CharField(max_length=150)
    end_point = models.CharField(max_length=150)
    total_distance_km = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)

    def __str__(self):
        return self.name


class RouteStop(TenantBaseModel):
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='stops')
    stop_name = models.CharField(max_length=150)
    stop_order = models.IntegerField(default=1)
    gps_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    gps_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    def __str__(self):
        return f"{self.route.name} - Stop {self.stop_order}: {self.stop_name}"


class Trip(TenantBaseModel):
    """
    Morning or afternoon route runs scheduled dynamically.
    """
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ]
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='trips')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='trips')
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='trips')
    trip_type = models.CharField(max_length=30, default='morning')  # morning, afternoon
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='scheduled')

    def __str__(self):
        return f"Trip: {self.route.name} ({self.trip_type}) on {self.status}"


class TripPassenger(TenantBaseModel):
    """
    Tracks passenger check-in times and boarding events.
    """
    STATUS_CHOICES = [
        ('waiting', 'Waiting'),
        ('boarded', 'Boarded'),
        ('dropped', 'Dropped')
    ]
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='passengers')
    student = models.ForeignKey('people.Person', on_delete=models.CASCADE, related_name='trip_checkins')
    boarded_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='waiting')

    def __str__(self):
        return f"{self.student.person_number} on {self.trip.route.name} ({self.status})"


# ==============================================================
# TRANSPORT SUBSCRIPTIONS & OPERATIONS
# ==============================================================

class TransportSubscription(TenantBaseModel):
    student = models.ForeignKey('people.Person', on_delete=models.CASCADE, related_name='transport_subscriptions')
    route = models.ForeignKey(Route, on_delete=models.CASCADE)
    stop = models.ForeignKey(RouteStop, on_delete=models.CASCADE)
    billing_type = models.CharField(max_length=30, default='monthly')  # monthly, termly, annual

    def __str__(self):
        return f"Sub for {self.student.person_number} (Route: {self.route.name})"


class VehicleLocation(TenantBaseModel):
    """
    Log caching vehicle live coordinates.
    """
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='locations')
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    speed = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.vehicle.registration_number}: {self.latitude},{self.longitude} at {self.timestamp}"


class FuelLog(TenantBaseModel):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='fuel_logs')
    liters = models.DecimalField(max_digits=8, decimal_places=2)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    refuel_date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"{self.vehicle.registration_number}: {self.liters}L on {self.refuel_date}"


class MaintenanceSchedule(TenantBaseModel):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='maintenance_schedules')
    description = models.CharField(max_length=200)
    scheduled_date = models.DateField()
    status = models.CharField(max_length=30, default='scheduled')

    def __str__(self):
        return f"Service for {self.vehicle.registration_number} on {self.scheduled_date}"
