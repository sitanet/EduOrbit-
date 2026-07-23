from django.test import TestCase
from django.utils import timezone
from datetime import time, timedelta
from backend.apps.tenants.models import Tenant, School
from backend.apps.people.models import Person
from backend.apps.attendance.models import (
    AttendancePolicy, AttendanceSource, AttendanceStatus,
    AttendanceType, AttendanceSession, AttendanceRecord, OfflineSyncQueue
)

class AttendanceManagementTests(TestCase):
    def setUp(self):
        # Create core configurations
        self.tenant = Tenant.objects.create(name="ATM Org")
        self.school = School.objects.create(tenant=self.tenant, name="ATM Primary", school_types=["primary"])
        
        # Policy
        self.policy = AttendancePolicy.objects.create(
            school=self.school,
            tenant=self.tenant,
            min_attendance_percentage=75.00,
            late_grace_period_minutes=15
        )
        
        # Lookups
        self.source = AttendanceSource.objects.create(name="Manual Input", code="manual")
        self.status_present = AttendanceStatus.objects.create(name="Present", code="present")
        self.type_daily = AttendanceType.objects.create(name="Daily Roll Call", code="daily")
        
        # Target Person profile
        self.person = Person.objects.create(
            tenant=self.tenant,
            person_number="P-40088",
            first_name="Diana",
            last_name="Prince",
            gender="female",
            date_of_birth="1990-08-14"
        )
        
        # Session
        self.session = AttendanceSession.objects.create(
            school=self.school,
            tenant=self.tenant,
            attendance_type=self.type_daily,
            date=timezone.now().date()
        )
        
    def test_attendance_session_marks_present(self):
        # Create attendance record
        record = AttendanceRecord.objects.create(
            session=self.session,
            person=self.person,
            tenant=self.tenant,
            status=self.status_present,
            source=self.source
        )
        
        # Verify
        self.assertEqual(record.person, self.person)
        self.assertEqual(record.status.code, "present")

    def test_offline_synchronization_queue(self):
        # Enqueue offline payload
        sync_log = OfflineSyncQueue.objects.create(
            tenant=self.tenant,
            payload={"student": "P-40088", "status": "present"},
            local_timestamp=timezone.now()
        )
        
        # Verify sync status
        self.assertEqual(sync_log.sync_status, "pending")
        self.assertIsNotNone(sync_log.client_uuid)
