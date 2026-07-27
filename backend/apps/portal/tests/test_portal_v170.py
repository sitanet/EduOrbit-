from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from backend.apps.tenants.models import Tenant, School
from backend.apps.people.models import Person, StudentProfile
from backend.apps.portal.models import ParentStudentRelationship
from backend.apps.portal.services.portals import ParentPortalService, StudentPortalService, StaffPortalService

class PortalV170TestCase(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Portal Tenant")
        self.school = School.objects.create(tenant=self.tenant, name="Apex International School")
        self.parent = Person.objects.create(
            tenant=self.tenant,
            person_number="PER-PAR-001",
            first_name="David",
            last_name="Beckham",
            date_of_birth="1975-05-02",
            gender="male"
        )
        self.student_person = Person.objects.create(
            tenant=self.tenant,
            person_number="PER-STU-001",
            first_name="Romeo",
            last_name="Beckham",
            date_of_birth="2002-09-01",
            gender="male"
        )
        self.student = StudentProfile.objects.create(
            tenant=self.tenant,
            person=self.student_person,
            student_number="STU-2026-00999",
            admission_number="ADM-00999",
            current_school=self.school
        )
        ParentStudentRelationship.objects.create(
            tenant=self.tenant,
            parent=self.parent,
            student=self.student,
            relationship_type="father"
        )
        self.staff = Person.objects.create(
            tenant=self.tenant,
            person_number="PER-STF-001",
            first_name="Sarah",
            last_name="Connor",
            date_of_birth="1980-01-01",
            gender="female"
        )
        self.client = APIClient()

    def test_portal_dashboard_services(self):
        # 1. Parent Dashboard Service
        parent_dash = ParentPortalService.get_parent_dashboard(parent_person=self.parent)
        self.assertEqual(parent_dash["total_children"], 1)
        self.assertEqual(parent_dash["children"][0]["student_number"], self.student.student_number)

        # 2. Student Dashboard Service
        student_dash = StudentPortalService.get_student_dashboard(student_profile=self.student)
        self.assertEqual(student_dash["student_number"], self.student.student_number)

        # 3. Staff Dashboard Service
        staff_dash = StaffPortalService.get_staff_dashboard(staff_person=self.staff)
        self.assertEqual(staff_dash["staff_id"], self.staff.person_number)

    def test_portal_api_endpoints(self):
        # 1. Parent Dashboard API
        p_url = f'/portal/api/v1/parent/dashboard/?parent_id={self.parent.id}'
        p_resp = self.client.get(p_url)
        self.assertEqual(p_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(p_resp.data["data"]["total_children"], 1)

        # 2. Student Dashboard API
        s_url = f'/portal/api/v1/student/dashboard/?student_id={self.student.id}'
        s_resp = self.client.get(s_url)
        self.assertEqual(s_resp.status_code, status.HTTP_200_OK)

        # 3. Staff Dashboard API
        stf_url = f'/portal/api/v1/staff/dashboard/?staff_id={self.staff.id}'
        stf_resp = self.client.get(stf_url)
        self.assertEqual(stf_resp.status_code, status.HTTP_200_OK)
