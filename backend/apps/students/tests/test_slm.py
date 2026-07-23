from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from backend.apps.tenants.models import Tenant, School
from backend.apps.people.models import Person, StudentProfile
from backend.apps.students.models import (
    SchoolHouse, StudentClub, student_state_machine, InvalidStateTransitionError,
    AcademicPlacementHistory, StudentTimeline
)
from backend.apps.academic.models import AcademicYear, EducationLevel, AcademicLevel, AcademicClass

class StudentLifecycleTests(TestCase):
    def setUp(self):
        # Create core configurations
        self.tenant = Tenant.objects.create(name="Beacon Org")
        self.school = School.objects.create(tenant=self.tenant, name="Beacon Academy", school_types=["primary"])
        
        # Academic years
        self.year = AcademicYear.objects.create(
            school=self.school,
            tenant=self.tenant,
            name="2026/2027 Year",
            code="2026-27-bea",
            start_date=timezone.now().date(),
            end_date=(timezone.now() + timedelta(days=365)).date(),
            status='active'
        )
        self.ed_level = EducationLevel.objects.create(school=self.school, tenant=self.tenant, name="Primary", code="pri")
        self.ac_level = AcademicLevel.objects.create(education_level=self.ed_level, tenant=self.tenant, name="Primary 1", code="pri1")
        self.ac_class = AcademicClass.objects.create(academic_level=self.ac_level, tenant=self.tenant, name="Primary 1 Gold")
        
        # Base profile
        self.person = Person.objects.create(
            tenant=self.tenant,
            person_number="P-10088",
            first_name="Max",
            last_name="Payne",
            gender="male",
            date_of_birth="2018-02-10"
        )
        self.student = StudentProfile.objects.create(
            person=self.person,
            tenant=self.tenant,
            student_number="STU-10088",
            current_school=self.school,
            enrollment_status="enrolled"
        )
        
    def test_state_machine_transition_validation(self):
        # State transitions checks
        current = 'pending'
        
        # 1. Valid Transition: pending -> active
        next_state = student_state_machine.transition(current, 'active')
        self.assertEqual(next_state, 'active')
        
        # 2. Invalid Transition: pending -> graduated should raise InvalidStateTransitionError
        with self.assertRaises(InvalidStateTransitionError):
            student_state_machine.transition(current, 'graduated')

    def test_academic_placement_history(self):
        # Create placement record
        placement = AcademicPlacementHistory.objects.create(
            student=self.student,
            tenant=self.tenant,
            academic_year=self.year,
            academic_class=self.ac_class
        )
        
        # Confirm student placement history counts
        self.assertEqual(self.student.placements.count(), 1)
        self.assertEqual(self.student.placements.first().academic_class, self.ac_class)
