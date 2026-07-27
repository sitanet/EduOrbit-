from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from backend.apps.tenants.models import Tenant, School
from backend.apps.people.models import Person
from backend.apps.attendance.models import AttendanceSession, AttendanceType, AttendanceRecord
from backend.apps.academic.services.attendance import AttendanceService

class AttendancePhase3TestCase(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Attendance Tenant")
        self.school = School.objects.create(tenant=self.tenant, name="Saint Jude High School")
        self.person = Person.objects.create(
            tenant=self.tenant,
            person_number="PER-ATT-101",
            first_name="Oliver",
            last_name="Queen",
            date_of_birth="2011-05-16",
            gender="male"
        )
        self.att_type = AttendanceType.objects.create(name="Daily Roll Call", code="daily")
        self.session = AttendanceSession.objects.create(
            tenant=self.tenant,
            school=self.school,
            attendance_type=self.att_type,
            date="2026-07-27"
        )
        self.client = APIClient()

    def test_attendance_service_mark_and_summary(self):
        # 1. Mark Present
        res = AttendanceService.mark_attendance(
            session=self.session,
            person=self.person,
            status_code="present",
            source_code="manual"
        )
        self.assertEqual(res["status"], "success")

        # 2. Get Summary
        summary = AttendanceService.get_attendance_summary(self.person)
        self.assertEqual(summary["total_sessions"], 1)
        self.assertEqual(summary["present_count"], 1)
        self.assertEqual(summary["attendance_percentage"], 100.0)

    def test_attendance_checkin_api(self):
        url = '/academic/api/v1/attendance/check-in/'
        payload = {
            "session_id": str(self.session.id),
            "person_id": str(self.person.id),
            "status_code": "present",
            "source_code": "qr"
        }
        resp = self.client.post(url, payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["status"], "success")
