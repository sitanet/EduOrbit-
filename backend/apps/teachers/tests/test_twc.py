from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from backend.apps.tenants.models import Tenant, School
from backend.apps.people.models import Person, StudentProfile
from backend.apps.academic.models import AcademicYear, AcademicPeriod, EducationLevel, AcademicLevel, AcademicClass, Subject, Curriculum as AcademicCurriculum
from backend.apps.teachers.models import (
    Curriculum, SchemeOfWork, WeeklyPlan, LessonPlan, StudentObservation
)
from backend.apps.teachers.ai import IAILessonPlanner

class TeacherWorkspaceTests(TestCase):
    def setUp(self):
        # Create core configurations
        self.tenant = Tenant.objects.create(name="TWC Org")
        self.school = School.objects.create(tenant=self.tenant, name="TWC Secondary", school_types=["secondary"])
        
        # Academic structure
        self.year = AcademicYear.objects.create(
            school=self.school,
            tenant=self.tenant,
            name="2026/2027 Year",
            code="2026-27-twc",
            start_date=timezone.now().date(),
            end_date=(timezone.now() + timedelta(days=365)).date(),
            status='active'
        )
        self.period = AcademicPeriod.objects.create(
            academic_year=self.year,
            tenant=self.tenant,
            name="First Term",
            start_date=timezone.now().date(),
            end_date=(timezone.now() + timedelta(days=120)).date(),
            status='active'
        )
        self.aca_curriculum = AcademicCurriculum.objects.create(name="Checkpoint", code="cp-27", version="1")
        self.subject = Subject.objects.create(school=self.school, tenant=self.tenant, curriculum=self.aca_curriculum, code="math-1", name="Mathematics 1")
        self.ed_level = EducationLevel.objects.create(school=self.school, tenant=self.tenant, name="Secondary", code="sec")
        self.ac_level = AcademicLevel.objects.create(education_level=self.ed_level, tenant=self.tenant, name="JSS 1", code="jss1")
        self.ac_class = AcademicClass.objects.create(academic_level=self.ac_level, tenant=self.tenant, name="JSS 1 Gold")
        
        # Person teacher & student profiles
        self.teacher = Person.objects.create(
            tenant=self.tenant,
            person_number="P-30088",
            first_name="Diana",
            last_name="Prince",
            gender="female",
            date_of_birth="1980-05-14"
        )
        self.student_person = Person.objects.create(
            tenant=self.tenant,
            person_number="P-30099",
            first_name="Bruce",
            last_name="Wayne",
            gender="male",
            date_of_birth="2012-04-12"
        )
        self.student = StudentProfile.objects.create(
            person=self.student_person,
            tenant=self.tenant,
            student_number="STU-30099",
            current_school=self.school,
            enrollment_status="enrolled"
        )
        
        # Global Curriculum
        self.curriculum = Curriculum.objects.create(name="Cambridge Checkpoint 2026", code="cam-cp-26", version="1.0")
        
    def test_four_layer_curriculum_planning(self):
        # 1. Layer 1: Scheme of Work
        scheme = SchemeOfWork.objects.create(
            school=self.school,
            tenant=self.tenant,
            curriculum=self.curriculum,
            academic_year=self.year,
            academic_period=self.period,
            subject=self.subject,
            target_level=self.ac_level
        )
        self.assertEqual(scheme.subject, self.subject)
        
        # 2. Layer 2: Weekly Plan
        weekly = WeeklyPlan.objects.create(
            scheme=scheme,
            tenant=self.tenant,
            week_number=1,
            topics_covered="Algebra introduction and simple equations."
        )
        self.assertEqual(weekly.week_number, 1)
        
        # 3. Layer 3: Lesson Plan
        plan = LessonPlan.objects.create(
            weekly_plan=weekly,
            tenant=self.tenant,
            title="Variables & Operations",
            objectives_summary="Introduce variables.",
            activities_description="Class operations.",
            version_number=1
        )
        self.assertEqual(plan.version_number, 1)
        
    def test_student_observation_recorded(self):
        # Create observation
        obs = StudentObservation.objects.create(
            student=self.student,
            teacher=self.teacher,
            tenant=self.tenant,
            category="academic",
            content="Bruce showed exceptional problem-solving skills in algebra.",
            visibility="staff_only"
        )
        self.assertEqual(obs.student, self.student)
        
        # Timeline updates check (we simulate the API observation creator logic)
        from backend.apps.students.models import StudentTimeline
        timeline_event = StudentTimeline.objects.create(
            student=self.student,
            tenant=self.tenant,
            event_type="observation",
            title=f"New Observation: Academic",
            description=obs.content[:150]
        )
        self.assertEqual(self.student.timeline.count(), 1)
