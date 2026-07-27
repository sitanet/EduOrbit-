from django.test import TestCase
from backend.apps.tenants.models import Tenant, School
from backend.apps.people.models import Person, StudentProfile
from backend.apps.students.models import (
    StudentStatusHistory, AcademicPlacementHistory, ClassPromotion, StudentTransfer
)
from backend.apps.students.services.student_number import StudentNumberGeneratorService
from backend.apps.students.services.lifecycle import StudentLifecycleService

class SISPhasedExecutionTestCase(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Academy SIS Phased")
        self.school = School.objects.create(tenant=self.tenant, name="Main Campus")
        self.person = Person.objects.create(
            tenant=self.tenant,
            person_number="PER-SIS-001",
            first_name="Miles",
            last_name="Morales",
            date_of_birth="2011-04-12",
            gender="male"
        )

    def test_phase1_student_foundation(self):
        stu_num = StudentNumberGeneratorService.generate_next_student_number(tenant=self.tenant)
        profile = StudentProfile.objects.create(
            tenant=self.tenant,
            person=self.person,
            student_number=stu_num,
            current_school=self.school,
            enrollment_status="pending"
        )
        self.assertEqual(profile.enrollment_status, "pending")
        self.assertTrue(profile.student_number.startswith("STU-"))

    def test_phase2_lifecycle_transition(self):
        person2 = Person.objects.create(
            tenant=self.tenant,
            person_number="PER-SIS-002",
            first_name="Gwen",
            last_name="Stacy",
            date_of_birth="2011-06-15",
            gender="female"
        )
        stu_num = StudentNumberGeneratorService.generate_next_student_number(tenant=self.tenant)
        profile = StudentProfile.objects.create(
            tenant=self.tenant,
            person=person2,
            student_number=stu_num,
            current_school=self.school,
            enrollment_status="pending"
        )
        res = StudentLifecycleService.transition_student_status(profile, "active", reason="Fees Cleared")
        self.assertEqual(res["new_status"], "active")

        # History check
        history_count = StudentStatusHistory.objects.filter(student=profile).count()
        self.assertEqual(history_count, 1)
