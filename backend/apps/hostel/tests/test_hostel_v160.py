from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from backend.apps.tenants.models import Tenant, School
from backend.apps.people.models import Person
from backend.apps.hostel.models import Hostel, HostelBlock, HostelRoom, HostelBed
from backend.apps.hostel.services.allocation import HostelApplicationService, RoomAllocationService, OccupancyService

class HostelV160TestCase(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Hostel Tenant")
        self.school = School.objects.create(tenant=self.tenant, name="Valhalla University Residential College")
        self.hostel = Hostel.objects.create(tenant=self.tenant, school=self.school, name="Thor Residential Hall", gender="male")
        self.block = HostelBlock.objects.create(tenant=self.tenant, hostel=self.hostel, name="Block A")
        self.room = HostelRoom.objects.create(tenant=self.tenant, block=self.block, room_number="101", capacity=2)
        self.bed = HostelBed.objects.create(tenant=self.tenant, room=self.room, bed_number="A", status="available")
        self.student = Person.objects.create(
            tenant=self.tenant,
            person_number="PER-HST-001",
            first_name="Arthur",
            last_name="Pendelton",
            date_of_birth="2005-03-20",
            gender="male"
        )
        self.client = APIClient()

    def test_hostel_application_and_allocation_service_flow(self):
        # 1. Submit Application
        app_res = HostelApplicationService.submit_application(student=self.student, hostel=self.hostel)
        self.assertEqual(app_res["status"], "success")

        # 2. Allocate Bed (Updates bed status & posts GL Journal entry)
        alloc_res = RoomAllocationService.allocate_bed(
            school=self.school, student=self.student, bed=self.bed, term_fee=850.00
        )
        self.assertEqual(alloc_res["status"], "success")
        self.bed.refresh_from_db()
        self.assertEqual(self.bed.status, "occupied")

        # 3. Occupancy Analytics
        occ = OccupancyService.get_hostel_occupancy(self.hostel)
        self.assertEqual(occ["total_beds"], 1)
        self.assertEqual(occ["occupied_beds"], 1)
        self.assertEqual(occ["occupancy_percentage"], 100.0)

    def test_hostel_api_endpoints(self):
        # 1. Hostel List API
        list_url = '/hostel/api/v1/hostels/'
        resp = self.client.get(list_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data["count"] > 0)

        # 2. Occupancy API
        occ_url = f'/hostel/api/v1/occupancy/?hostel_id={self.hostel.id}'
        occ_resp = self.client.get(occ_url)
        self.assertEqual(occ_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(occ_resp.data["data"]["hostel_name"], self.hostel.name)
