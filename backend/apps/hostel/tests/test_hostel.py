from django.test import TestCase
from django.utils import timezone
from datetime import date, timedelta
from backend.apps.tenants.models import Tenant, School
from backend.apps.people.models import Person
from backend.apps.hostel.models import (
    Hostel, HostelBlock, HostelRoom, HostelBed, BedAllocation, HostelRollCall, RoomInspection
)

class HostelPlatformTests(TestCase):
    def setUp(self):
        # Create core configurations
        self.tenant = Tenant.objects.create(name="EHRM Org")
        self.school = School.objects.create(tenant=self.tenant, name="EHRM Boarding School", school_types=["secondary"])
        
        # Student Person profile
        self.student = Person.objects.create(
            tenant=self.tenant,
            person_number="P-88001",
            first_name="Ron",
            last_name="Weasley",
            gender="male",
            date_of_birth="2011-03-01"
        )
        
        # Hostel residential structures
        self.hostel = Hostel.objects.create(school=self.school, tenant=self.tenant, name="Gryffindor Dorm", gender="male")
        self.block = HostelBlock.objects.create(hostel=self.hostel, tenant=self.tenant, name="Tower A")
        self.room = HostelRoom.objects.create(block=self.block, tenant=self.tenant, room_number="R-201", capacity=4)
        self.bed = HostelBed.objects.create(room=self.room, tenant=self.tenant, bed_number="Bed-01", status="available")

    def test_bed_allocation_occupancy_lifecycle(self):
        # Initial allocation
        alloc = BedAllocation.objects.create(
            bed=self.bed,
            student=self.student,
            tenant=self.tenant,
            status="active"
        )
        self.assertEqual(alloc.status, "active")
        
        # Mark bed occupied
        self.bed.status = "occupied"
        self.bed.save()
        self.assertEqual(self.bed.status, "occupied")

    def test_nightly_rollcall_marks(self):
        rc = HostelRollCall.objects.create(
            student=self.student,
            tenant=self.tenant,
            date=date.today(),
            status="present"
        )
        self.assertEqual(rc.status, "present")

    def test_room_hygiene_inspection_scoring(self):
        inspection = RoomInspection.objects.create(
            room=self.room,
            tenant=self.tenant,
            score=9.50
        )
        self.assertEqual(inspection.score, 9.50)
