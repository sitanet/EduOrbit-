from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from backend.apps.tenants.models import Tenant, School
from backend.apps.people.models import Person
from backend.apps.transport.models import VehicleCategory, Vehicle, Driver, Route, RouteStop, Trip
from backend.apps.transport.services.fleet import FleetService, RouteService, TransportAttendanceService, TransportFeeService

class TransportV170TestCase(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Transport Tenant")
        self.school = School.objects.create(tenant=self.tenant, name="Saint Jude High School")
        self.category = VehicleCategory.objects.create(tenant=self.tenant, name="School Bus")
        self.vehicle = Vehicle.objects.create(
            tenant=self.tenant, category=self.category, registration_number="BUS-001", plate_number="KJA-123-AA", capacity=30
        )
        self.driver_person = Person.objects.create(
            tenant=self.tenant, person_number="PER-DRV-001", first_name="Michael", last_name="Knight", date_of_birth="1982-04-10", gender="male"
        )
        self.driver = Driver.objects.create(tenant=self.tenant, person=self.driver_person, license_number="DL-998877")
        self.route = Route.objects.create(
            tenant=self.tenant, name="Route A - Central Suburbs", start_point="Main Depot", end_point="Campus Gate 1", total_distance_km=15.5
        )
        self.stop = RouteStop.objects.create(tenant=self.tenant, route=self.route, stop_name="Oak Street Junction", stop_order=1)
        self.trip = Trip.objects.create(
            tenant=self.tenant, route=self.route, vehicle=self.vehicle, driver=self.driver, trip_type="morning", status="in_progress"
        )
        self.student = Person.objects.create(
            tenant=self.tenant, person_number="PER-STU-888", first_name="Logan", last_name="Roy", date_of_birth="2007-11-20", gender="male"
        )
        self.client = APIClient()

    def test_fleet_route_attendance_and_fee_services(self):
        # 1. Fleet Vehicle Registration
        veh_res = FleetService.register_vehicle(
            school=self.school, category=self.category, registration_number="BUS-002", plate_number="KJA-456-BB", capacity=40
        )
        self.assertEqual(veh_res["status"], "success")

        # 2. Student Bus Boarding Check-In (Triggers Parent Notification)
        chk_res = TransportAttendanceService.check_in_student(trip=self.trip, student=self.student)
        self.assertEqual(chk_res["status"], "success")
        self.assertEqual(chk_res["status_name"], "boarded")

        # 3. Transport Fee Generation (Posts GL Journal Entry)
        fee_res = TransportFeeService.generate_transport_fee(
            school=self.school, student=self.student, route=self.route, term_fee=350.00
        )
        self.assertEqual(fee_res["status"], "success")
        self.assertEqual(fee_res["term_fee"], 350.00)

    def test_transport_api_endpoints(self):
        # 1. Routes API
        r_url = '/transport/api/v1/routes/'
        r_resp = self.client.get(r_url)
        self.assertEqual(r_resp.status_code, status.HTTP_200_OK)
        self.assertTrue(r_resp.data["count"] > 0)

        # 2. Check-in API
        chk_url = '/transport/api/v1/check-in/'
        payload = {
            "trip_id": str(self.trip.id),
            "student_id": str(self.student.id)
        }
        chk_resp = self.client.post(chk_url, payload, format='json')
        self.assertEqual(chk_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(chk_resp.data["status"], "success")
