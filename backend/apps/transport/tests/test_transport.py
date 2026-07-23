from django.test import TestCase
from django.utils import timezone
from datetime import date, timedelta
from backend.apps.tenants.models import Tenant, School
from backend.apps.people.models import Person
from backend.apps.transport.models import (
    VehicleCategory, Vehicle, Driver, Route, RouteStop, Trip, TripPassenger, TransportSubscription, VehicleLocation
)

class TransportPlatformTests(TestCase):
    def setUp(self):
        # Create core configurations
        self.tenant = Tenant.objects.create(name="ETFM Org")
        self.school = School.objects.create(tenant=self.tenant, name="ETFM High School", school_types=["secondary"])
        
        # Driver Person profile
        self.driver_person = Person.objects.create(
            tenant=self.tenant,
            person_number="P-77001",
            first_name="Max",
            last_name="Rockatansky",
            gender="male",
            date_of_birth="1980-06-23"
        )
        self.driver = Driver.objects.create(
            person=self.driver_person,
            tenant=self.tenant,
            license_number="DL-99088"
        )
        
        # Student Person profile
        self.student = Person.objects.create(
            tenant=self.tenant,
            person_number="P-77002",
            first_name="Furiosa",
            last_name="Imperator",
            gender="female",
            date_of_birth="2012-05-14"
        )
        
        # Fleet & Routes
        self.category = VehicleCategory.objects.create(tenant=self.tenant, name="School Bus")
        self.vehicle = Vehicle.objects.create(
            category=self.category,
            tenant=self.tenant,
            registration_number="BUS-MAD-01",
            plate_number="MAD-MAX-1",
            capacity=40
        )
        
        self.route = Route.objects.create(
            tenant=self.tenant,
            name="Main Northern Route",
            start_point="School Garage",
            end_point="City Center",
            total_distance_km=15.50
        )
        self.stop = RouteStop.objects.create(
            route=self.route,
            tenant=self.tenant,
            stop_name="Zone A Junction",
            stop_order=1
        )
        
        # Trip
        self.trip = Trip.objects.create(
            route=self.route,
            vehicle=self.vehicle,
            driver=self.driver,
            tenant=self.tenant,
            trip_type="morning",
            status="scheduled"
        )

    def test_passenger_boarding_status_changes(self):
        passenger = TripPassenger.objects.create(
            trip=self.trip,
            student=self.student,
            tenant=self.tenant,
            status="waiting"
        )
        self.assertEqual(passenger.status, "waiting")
        
        # Board bus
        passenger.status = "boarded"
        passenger.boarded_time = timezone.now()
        passenger.save()
        self.assertEqual(passenger.status, "boarded")
        self.assertIsNotNone(passenger.boarded_time)

    def test_vehicle_live_location_logging(self):
        loc = VehicleLocation.objects.create(
            vehicle=self.vehicle,
            tenant=self.tenant,
            latitude=6.524400,
            longitude=3.379200,
            speed=45.00
        )
        self.assertEqual(loc.speed, 45.00)
