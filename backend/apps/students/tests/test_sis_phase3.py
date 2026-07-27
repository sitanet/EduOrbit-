from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from backend.apps.tenants.models import Tenant, School
from backend.apps.people.models import Person, StudentProfile
from backend.apps.academic.models import AcademicYear, EducationLevel, AcademicLevel, AcademicClass
from backend.apps.students.services.enrollment import EnrollmentService

class SISPhase3EnrollmentTestCase(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test SIS Phase 3 Tenant")
        self.school = School.objects.create(tenant=self.tenant, name="Kings College")
        self.year = AcademicYear.objects.create(
            tenant=self.tenant,
            school=self.school,
            name="2026/2027",
            code="2026-2027",
            start_date="2026-09-01",
            end_date="2027-07-15"
        )
        self.education_level = EducationLevel.objects.create(
            tenant=self.tenant,
            school=self.school,
            name="Secondary Education",
            code="secondary"
        )
        self.academic_level = AcademicLevel.objects.create(
            tenant=self.tenant,
            education_level=self.education_level,
            name="JSS 1",
            code="jss-1"
        )
        self.class1 = AcademicClass.objects.create(
            tenant=self.tenant,
            academic_level=self.academic_level,
            name="JSS 1 Red"
        )
        self.class2 = AcademicClass.objects.create(
            tenant=self.tenant,
            academic_level=self.academic_level,
            name="JSS 2 Blue"
        )
        self.person = Person.objects.create(
            tenant=self.tenant,
            person_number="PER-ENR-001",
            first_name="Arthur",
            last_name="Curry",
            date_of_birth="2012-07-11",
            gender="male"
        )
        self.client = APIClient()

    def test_enrollment_service_full_flow(self):
        # 1. Enroll Student
        res = EnrollmentService.enroll_student(
            person=self.person,
            school=self.school,
            academic_year=self.year,
            academic_class=self.class1,
            enrollment_type='new'
        )
        self.assertEqual(res["status"], "success")
        student = StudentProfile.objects.get(id=res["student_profile_id"])

        # 2. Promote Student
        promo_res = EnrollmentService.promote_student(student, self.class1, self.class2)
        self.assertEqual(promo_res["status"], "success")

        # 3. Withdraw Student
        with_res = EnrollmentService.withdraw_student(student, reason="Relocation")
        self.assertEqual(with_res["status"], "success")
        student.refresh_from_db()
        self.assertEqual(student.enrollment_status, "withdrawn")

    def test_enrollment_api_endpoints(self):
        # 1. Enroll API
        url = '/students/api/v1/enroll/'
        payload = {
            "school_id": str(self.school.id),
            "first_name": "Barry",
            "last_name": "Allen",
            "gender": "male",
            "date_of_birth": "2012-09-30"
        }
        resp = self.client.post(url, payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        student_id = resp.data["data"]["student_id"]

        # 2. Student Record API
        rec_url = f'/students/api/v1/student-record/?student_id={student_id}'
        rec_resp = self.client.get(rec_url)
        self.assertEqual(rec_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(rec_resp.data["data"]["name"], "Barry Allen")
