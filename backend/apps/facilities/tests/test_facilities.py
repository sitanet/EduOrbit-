from django.test import TestCase
from django.utils import timezone
from datetime import date
from decimal import Decimal
from backend.apps.tenants.models import Tenant, School
from backend.apps.people.models import Person
from backend.apps.facilities.models import (
    Building, Floor, Room, Facility, WorkRequest, WorkOrder, WorkLog, FacilityMaintenancePlan, FacilityMaintenanceSchedule, Inspection, UtilityMeter, UtilityReading
)

class FacilitiesPlatformTests(TestCase):
    def setUp(self):
        # Create core configurations
        self.tenant = Tenant.objects.create(name="EFMWO Org")
        self.school = School.objects.create(tenant=self.tenant, name="EFMWO High School", school_types=["secondary"])
        
        # Staff Person profile
        self.staff_person = Person.objects.create(
            tenant=self.tenant,
            person_number="P-303001",
            first_name="Arthur",
            last_name="Dent",
            gender="male",
            date_of_birth="1979-10-12"
        )
        
        # Buildings & layouts
        self.building = Building.objects.create(school=self.school, tenant=self.tenant, name="Science Block", code="SCI-BLK")
        self.floor = Floor.objects.create(building=self.building, tenant=self.tenant, name="First Floor")
        self.room = Room.objects.create(floor=self.floor, tenant=self.tenant, room_number="R-101", room_type="laboratory")
        
        # Utility meter
        self.meter = UtilityMeter.objects.create(building=self.building, tenant=self.tenant, meter_type="electricity")

    def test_work_order_lifecycle(self):
        req = WorkRequest.objects.create(
            requester=self.staff_person,
            room=self.room,
            tenant=self.tenant,
            description="Broken lab sink tap",
            priority="high"
        )
        order = WorkOrder.objects.create(
            request=req,
            tenant=self.tenant,
            status="assigned"
        )
        self.assertEqual(order.status, "assigned")
        
        # Update progress
        order.status = "in_progress"
        order.save()
        log = WorkLog.objects.create(order=order, tenant=self.tenant, action="Started plumbing repairs")
        self.assertEqual(order.status, "in_progress")
        self.assertEqual(log.action, "Started plumbing repairs")

    def test_preventive_maintenance_scheduler(self):
        plan = FacilityMaintenancePlan.objects.create(
            tenant=self.tenant,
            name="Generator Monthly Servicing",
            recurrence="monthly"
        )
        sched = FacilityMaintenanceSchedule.objects.create(
            plan=plan,
            tenant=self.tenant,
            next_due_date=date.today()
        )
        self.assertEqual(sched.plan.name, "Generator Monthly Servicing")

    def test_utility_readings_posting(self):
        reading = UtilityReading.objects.create(
            meter=self.meter,
            tenant=self.tenant,
            reading_value=Decimal("4500.50"),
            reading_date=date.today()
        )
        self.assertEqual(reading.reading_value, Decimal("4500.50"))
