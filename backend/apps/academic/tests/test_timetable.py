from django.test import TestCase
from backend.apps.tenants.models import Tenant, School
from backend.apps.people.models import Person
from backend.apps.academic.models import (
    AcademicYear, EducationLevel, AcademicLevel, AcademicClass, Curriculum, Subject
)
from backend.apps.timetable.models import (
    BellSchedule, TimeSlot, Resource, ScheduleType, Lesson, Schedule
)
from backend.apps.academic.services.timetable import TimetableGenerationService, ConflictDetectionService

class TimetableSchedulingTestCase(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Timetable Tenant")
        self.school = School.objects.create(tenant=self.tenant, name="Tech Academy")
        self.curriculum = Curriculum.objects.create(name="NC", code="NC26", version="1")
        self.subject = Subject.objects.create(
            tenant=self.tenant, school=self.school, curriculum=self.curriculum,
            code="MTH-1", name="Maths", credit_units=3
        )
        self.education_level = EducationLevel.objects.create(
            tenant=self.tenant, school=self.school, name="Secondary", code="sec"
        )
        self.academic_level = AcademicLevel.objects.create(
            tenant=self.tenant, education_level=self.education_level, name="Form 1", code="f1"
        )
        self.academic_class = AcademicClass.objects.create(
            tenant=self.tenant, academic_level=self.academic_level, name="Form 1 A"
        )
        self.teacher = Person.objects.create(
            tenant=self.tenant, person_number="PER-TCH-999", first_name="Alan", last_name="Turing",
            date_of_birth="1912-06-23", gender="male"
        )
        self.bell = BellSchedule.objects.create(
            tenant=self.tenant, school=self.school, name="Senior Bell"
        )
        self.slot1 = TimeSlot.objects.create(
            tenant=self.tenant, bell_schedule=self.bell, day_of_week="monday",
            start_time="08:00:00", end_time="08:40:00"
        )
        self.resource = Resource.objects.create(
            tenant=self.tenant, school=self.school, name="Lab 1", resource_type="lab"
        )
        self.sched_type = ScheduleType.objects.create(name="Academic Lesson", code="lesson")
        self.lesson = Lesson.objects.create(
            tenant=self.tenant, school=self.school, subject=self.subject,
            teacher=self.teacher, academic_class=self.academic_class
        )

    def test_schedule_creation_and_conflict_detection(self):
        # 1. Create Schedule Slot
        res = TimetableGenerationService.create_schedule_slot(
            school=self.school,
            schedule_type=self.sched_type,
            lesson=self.lesson,
            resource=self.resource,
            time_slot=self.slot1,
            title="Maths Lab"
        )
        self.assertEqual(res["status"], "success")

        # 2. Test Conflict Detection (Same teacher at same timeslot)
        conf_res = TimetableGenerationService.create_schedule_slot(
            school=self.school,
            schedule_type=self.sched_type,
            lesson=self.lesson,
            resource=self.resource,
            time_slot=self.slot1,
            title="Maths Lab 2"
        )
        self.assertEqual(conf_res["status"], "error")
        self.assertTrue(conf_res["has_conflicts"])
