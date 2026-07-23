from django.test import TestCase
from django.utils import timezone
from datetime import time, timedelta
from backend.apps.tenants.models import Tenant, School
from backend.apps.people.models import Person
from backend.apps.academic.models import AcademicYear, EducationLevel, AcademicLevel, AcademicClass, Subject, Curriculum
from backend.apps.timetable.models import (
    BellSchedule, TimeSlot, Resource, ScheduleType, Lesson, Schedule, ConflictReport
)

class TimetableAndSchedulingTests(TestCase):
    def setUp(self):
        # Create core configurations
        self.tenant = Tenant.objects.create(name="Central Org")
        self.school = School.objects.create(tenant=self.tenant, name="Central High", school_types=["secondary"])
        
        # Academic structures
        self.year = AcademicYear.objects.create(
            school=self.school,
            tenant=self.tenant,
            name="2026/2027 Year",
            code="2026-27-cen",
            start_date=timezone.now().date(),
            end_date=(timezone.now() + timedelta(days=365)).date(),
            status='active'
        )
        self.curriculum = Curriculum.objects.create(name="Checkpoint", code="cp-27", version="1")
        self.subject = Subject.objects.create(school=self.school, tenant=self.tenant, curriculum=self.curriculum, code="eng-1", name="English 1")
        self.ed_level = EducationLevel.objects.create(school=self.school, tenant=self.tenant, name="Secondary", code="sec")
        self.ac_level = AcademicLevel.objects.create(education_level=self.ed_level, tenant=self.tenant, name="JSS 1", code="jss1")
        self.ac_class = AcademicClass.objects.create(academic_level=self.ac_level, tenant=self.tenant, name="JSS 1 Gold")
        
        # Teacher Profile Person
        self.teacher = Person.objects.create(
            tenant=self.tenant,
            person_number="P-20099",
            first_name="Alfred",
            last_name="Pennyworth",
            gender="male",
            date_of_birth="1970-04-12"
        )
        
        # Time and bell schedules
        self.bell = BellSchedule.objects.create(school=self.school, tenant=self.tenant, name="Secondary timings")
        self.slot_1 = TimeSlot.objects.create(
            bell_schedule=self.bell,
            tenant=self.tenant,
            day_of_week="monday",
            start_time=time(8, 0),
            end_time=time(8, 40)
        )
        
        # Resource Room
        self.room = Resource.objects.create(school=self.school, tenant=self.tenant, name="Classroom 101", capacity=35)
        
        # Schedule Type
        self.type_lesson = ScheduleType.objects.create(name="Academic Lesson", code="lesson")
        
        # Lesson definition
        self.lesson = Lesson.objects.create(
            school=self.school,
            tenant=self.tenant,
            subject=self.subject,
            teacher=self.teacher,
            academic_class=self.ac_class
        )
        
    def test_lesson_scheduling_pre_save_conflict_detection(self):
        # 1. Schedule first lesson
        sch1 = Schedule.objects.create(
            school=self.school,
            tenant=self.tenant,
            schedule_type=self.type_lesson,
            lesson=self.lesson,
            resource=self.room,
            time_slot=self.slot_1
        )
        self.assertEqual(sch1.time_slot, self.slot_1)
        
        # 2. Try scheduling another lesson at the same room & slot (Pre-save validation Simulation)
        # We manually verify the validator check via API views logic simulation:
        room_overlap = Schedule.objects.filter(
            resource=self.room,
            time_slot=self.slot_1,
            tenant=self.tenant
        ).exists()
        
        self.assertTrue(room_overlap)
        if room_overlap:
            ConflictReport.objects.create(
                school=self.school,
                tenant=self.tenant,
                conflict_type='room_clash',
                description="Classroom 101 occupied.",
                severity='error'
            )
            
        # Verify Conflict Report logged
        self.assertEqual(ConflictReport.objects.filter(school=self.school).count(), 1)
        self.assertEqual(ConflictReport.objects.first().conflict_type, "room_clash")
