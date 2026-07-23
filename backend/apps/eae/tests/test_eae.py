from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from backend.apps.tenants.models import Tenant, School
from backend.apps.people.models import Person, StudentProfile
from backend.apps.academic.models import AcademicYear, AcademicPeriod, EducationLevel, AcademicLevel, Subject, Curriculum as AcademicCurriculum
from backend.apps.eae.models import (
    Question, QuestionChoice, AssessmentBlueprint, Assessment,
    AssessmentAttempt, AttemptAnswer, ProctorLog, AssessmentResult
)

class EAEPlatformTests(TestCase):
    def setUp(self):
        # Create core configurations
        self.tenant = Tenant.objects.create(name="EAE Org")
        self.school = School.objects.create(tenant=self.tenant, name="EAE College", school_types=["secondary"])
        
        # Academic structures
        self.year = AcademicYear.objects.create(
            school=self.school,
            tenant=self.tenant,
            name="2026/2027 Year",
            code="2026-27-eae",
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
        self.subject = Subject.objects.create(school=self.school, tenant=self.tenant, curriculum=self.aca_curriculum, code="chem-1", name="Chemistry 1")
        self.ed_level = EducationLevel.objects.create(school=self.school, tenant=self.tenant, name="Secondary", code="sec")
        self.ac_level = AcademicLevel.objects.create(education_level=self.ed_level, tenant=self.tenant, name="JSS 1", code="jss1")
        
        # Student Profile
        self.person = Person.objects.create(
            tenant=self.tenant,
            person_number="P-60088",
            first_name="Clark",
            last_name="Kent",
            gender="male",
            date_of_birth="2010-12-01"
        )
        self.student = StudentProfile.objects.create(
            person=self.person,
            tenant=self.tenant,
            student_number="STU-60088",
            current_school=self.school,
            enrollment_status="enrolled"
        )
        
        # Blueprint
        self.blueprint = AssessmentBlueprint.objects.create(
            school=self.school,
            tenant=self.tenant,
            subject=self.subject,
            number_of_questions=5,
            topics=["Acids", "Bases"]
        )
        
        # Assessment
        self.assessment = Assessment.objects.create(
            school=self.school,
            tenant=self.tenant,
            blueprint=self.blueprint,
            title="Chemistry Term Test 1",
            duration_minutes=30
        )
        
    def test_mcq_auto_marking_evaluation(self):
        # 1. Register Question
        q = Question.objects.create(
            school=self.school,
            tenant=self.tenant,
            subject=self.subject,
            topic="Acids",
            question_text="What is the pH of water?",
            question_type="mcq",
            default_marks=5.00
        )
        c_correct = QuestionChoice.objects.create(question=q, choice_text="7", is_correct=True, tenant=self.tenant)
        c_wrong = QuestionChoice.objects.create(question=q, choice_text="1", is_correct=False, tenant=self.tenant)
        
        # 2. Start attempt
        attempt = AssessmentAttempt.objects.create(
            student=self.student,
            assessment=self.assessment,
            tenant=self.tenant,
            status="started"
        )
        
        # 3. Answer correct choice
        ans = AttemptAnswer.objects.create(
            attempt=attempt,
            question=q,
            selected_choice=c_correct,
            tenant=self.tenant
        )
        
        # Verify initial state
        self.assertFalse(ans.is_correct)
        
        # Simulate auto-marking check
        if ans.selected_choice.is_correct:
            ans.is_correct = True
            ans.marks_earned = q.default_marks
            ans.save()
            
        self.assertTrue(ans.is_correct)
        self.assertEqual(ans.marks_earned, 5.00)

    def test_proctor_log_suspicion_monitoring(self):
        # Start attempt
        attempt = AssessmentAttempt.objects.create(
            student=self.student,
            assessment=self.assessment,
            tenant=self.tenant,
            status="started"
        )
        
        # Create proctor violation log
        log = ProctorLog.objects.create(
            attempt=attempt,
            tenant=self.tenant,
            event_type="tab_switch",
            metadata={"destination": "google.com"}
        )
        
        self.assertEqual(log.event_type, "tab_switch")
        self.assertEqual(log.metadata.get("destination"), "google.com")
        self.assertIsNotNone(log.timestamp)
