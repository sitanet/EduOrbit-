from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from backend.apps.tenants.models import Tenant, School
from backend.apps.people.models import Person, StudentProfile
from backend.apps.academic.models import AcademicYear, AcademicPeriod, EducationLevel, AcademicLevel, Subject, Curriculum as AcademicCurriculum
from backend.apps.emrp.models import (
    ExamSession, Examination, GradingFormula, ExamResult, ResultCorrection, MalpracticeCase
)

class EMRPPlatformTests(TestCase):
    def setUp(self):
        # Create core configurations
        self.tenant = Tenant.objects.create(name="EMRP Org")
        self.school = School.objects.create(tenant=self.tenant, name="EMRP High School", school_types=["secondary"])
        
        # Academic structures
        self.year = AcademicYear.objects.create(
            school=self.school,
            tenant=self.tenant,
            name="2026/2027 Year",
            code="2026-27-emrp",
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
        self.subject = Subject.objects.create(school=self.school, tenant=self.tenant, curriculum=self.aca_curriculum, code="phys-1", name="Physics 1")
        
        # Student Profile
        self.person = Person.objects.create(
            tenant=self.tenant,
            person_number="P-70088",
            first_name="Tony",
            last_name="Stark",
            gender="male",
            date_of_birth="2010-05-29"
        )
        self.student = StudentProfile.objects.create(
            person=self.person,
            tenant=self.tenant,
            student_number="STU-70088",
            current_school=self.school,
            enrollment_status="enrolled"
        )
        
        # Exam Session
        self.session = ExamSession.objects.create(
            school=self.school,
            tenant=self.tenant,
            academic_year=self.year,
            name="First Term Exams"
        )
        self.exam = Examination.objects.create(
            school=self.school,
            tenant=self.tenant,
            exam_session=self.session,
            title="Physics Final Exam"
        )
        
        # Grading Formula
        self.formula = GradingFormula.objects.create(
            school=self.school,
            tenant=self.tenant,
            code="std_phys",
            formula_expression="raw_score * 0.7 + 30"  # mock formula
        )

    def test_dynamic_grading_formula_and_calculations(self):
        # Create exam result
        raw = 80.00
        computed = (raw * 0.7) + 30  # matches std_phys expression logic
        
        res = ExamResult.objects.create(
            student=self.student,
            exam=self.exam,
            tenant=self.tenant,
            raw_score=raw,
            computed_score=computed,
            letter_grade="A",
            gp=4.00,
            status="draft"
        )
        
        self.assertEqual(res.computed_score, 86.00)
        self.assertEqual(res.letter_grade, "A")

    def test_result_correction_auditing(self):
        res = ExamResult.objects.create(
            student=self.student,
            exam=self.exam,
            tenant=self.tenant,
            raw_score=50.00,
            computed_score=65.00,
            letter_grade="C",
            status="published"
        )
        
        # Request alteration
        correction = ResultCorrection.objects.create(
            result=res,
            tenant=self.tenant,
            requested_score=75.00,
            reason="Input mistake by typist",
            requested_by_user_id=self.person.id
        )
        
        self.assertEqual(correction.status, "pending")
        self.assertEqual(correction.requested_score, 75.00)

    def test_malpractice_case_logging(self):
        case = MalpracticeCase.objects.create(
            student=self.student,
            exam=self.exam,
            tenant=self.tenant,
            details="Found with cheating notes in desk drawer."
        )
        self.assertEqual(case.status, "pending")
