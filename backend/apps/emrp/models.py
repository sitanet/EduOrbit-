import uuid
from django.db import models
from django.utils import timezone
from backend.apps.core.models import TenantBaseModel, PlatformBaseModel

# ==============================================================
# SESSIONS, EXAMINATIONS, & SCHEDULING
# ==============================================================

class ExamSession(TenantBaseModel):
    """
    Groups examination runs under an Academic Year (First Term, Semester).
    """
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE)
    academic_year = models.ForeignKey('academic.AcademicYear', on_delete=models.CASCADE)
    name = models.CharField(max_length=150)  # e.g., First Term Exams

    def __str__(self):
        return f"{self.name} ({self.academic_year.name})"


class Examination(TenantBaseModel):
    """
    The official Examination header (e.g. Science Term Exam).
    """
    STATUS = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('approved', 'Approved'),
        ('published', 'Published')
    ]
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE)
    exam_session = models.ForeignKey(ExamSession, on_delete=models.CASCADE, related_name='examinations')
    title = models.CharField(max_length=150)
    status = models.CharField(max_length=20, choices=STATUS, default='draft')

    def __str__(self):
        return self.title


class ExaminationPaper(TenantBaseModel):
    """
    Binds an EAE Assessment definition to an Examination run with weights parameters.
    """
    exam = models.ForeignKey(Examination, on_delete=models.CASCADE, related_name='papers')
    assessment = models.ForeignKey('eae.Assessment', on_delete=models.CASCADE)
    formula_weight = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)

    def __str__(self):
        return f"{self.assessment.title} in {self.exam.title}"


class ExaminationSchedule(TenantBaseModel):
    """
    Rooms and timing slots coordinates invigilations.
    """
    paper = models.ForeignKey(ExaminationPaper, on_delete=models.CASCADE, related_name='schedules')
    start_time = models.DateTimeField(default=timezone.now)
    duration_minutes = models.IntegerField(default=60)
    room = models.ForeignKey('academic.AcademicResource', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Schedule for {self.paper} on {self.start_time}"


# ==============================================================
# CANDIDATES, SEATINGS, & MALPRACTICE INCIDENTS
# ==============================================================

class CandidateRegistration(TenantBaseModel):
    """
    Enrolled candidate profiles.
    """
    student = models.ForeignKey('people.StudentProfile', on_delete=models.CASCADE)
    exam = models.ForeignKey(Examination, on_delete=models.CASCADE, related_name='candidates')
    registered_at = models.DateTimeField(default=timezone.now)
    eligible = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.student.student_number} registered in {self.exam.title}"


class SeatingArrangement(TenantBaseModel):
    registration = models.ForeignKey(CandidateRegistration, on_delete=models.CASCADE, related_name='seatings')
    seat_number = models.CharField(max_length=50)

    def __str__(self):
        return f"Seat {self.seat_number} - Candidate: {self.registration.student.student_number}"


class InvigilatorAssignment(TenantBaseModel):
    schedule = models.ForeignKey(ExaminationSchedule, on_delete=models.CASCADE, related_name='invigilators')
    teacher = models.ForeignKey('people.TeacherProfile', on_delete=models.CASCADE)

    def __str__(self):
        return f"Invigilator: {self.teacher.employee_number}"


class MalpracticeCase(TenantBaseModel):
    STATUS = [
        ('pending', 'Pending Review'),
        ('under_investigation', 'Under Investigation'),
        ('resolved', 'Resolved')
    ]
    student = models.ForeignKey('people.StudentProfile', on_delete=models.CASCADE)
    exam = models.ForeignKey(Examination, on_delete=models.CASCADE)
    details = models.TextField()
    status = models.CharField(max_length=30, choices=STATUS, default='pending')

    def __str__(self):
        return f"Case: {self.student.student_number} ({self.status})"


# ==============================================================
# FORMULAS, RESULTS PIPELINE, & AUDIT CORRECTIONS
# ==============================================================

class GradingFormula(TenantBaseModel):
    """
    Data-driven mathematical grading formula configurations (e.g. 'ca*0.4 + exam*0.6').
    """
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE)
    code = models.CharField(max_length=50, unique=True)
    formula_expression = models.CharField(max_length=255)  # formula parsed during marks calculation

    def __str__(self):
        return self.code


class ExamResult(TenantBaseModel):
    """
    Saves computed score totals, letter grade, and approval workflow status.
    """
    STATUS = [
        ('draft', 'Draft'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('locked', 'Locked'),
        ('published', 'Published')
    ]
    student = models.ForeignKey('people.StudentProfile', on_delete=models.CASCADE)
    exam = models.ForeignKey(Examination, on_delete=models.CASCADE)
    raw_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    computed_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    letter_grade = models.CharField(max_length=10, blank=True)
    gp = models.DecimalField(max_digits=4, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS, default='draft')

    def __str__(self):
        return f"{self.student.student_number} -> {self.computed_score} ({self.status})"


class ResultVersion(TenantBaseModel):
    """
    Historical log storing previous points configurations.
    """
    result = models.ForeignKey(ExamResult, on_delete=models.CASCADE, related_name='versions')
    version_number = models.IntegerField(default=1)
    score = models.DecimalField(max_digits=5, decimal_places=2)
    modified_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"v{self.version_number} score: {self.score}"


class ResultCorrection(TenantBaseModel):
    """
    Audit log alteration requests lines.
    """
    result = models.ForeignKey(ExamResult, on_delete=models.CASCADE, related_name='corrections')
    requested_score = models.DecimalField(max_digits=5, decimal_places=2)
    status = models.CharField(max_length=20, default='pending')  # pending, approved, rejected
    reason = models.TextField()
    requested_by_user_id = models.UUIDField()

    def __str__(self):
        return f"Correction for {self.result.student.student_number} ({self.status})"


# ==============================================================
# PROMOTIONS PREVIEW & TRANSCRIPTS RECORDS
# ==============================================================

class PromotionRecommendation(TenantBaseModel):
    student = models.ForeignKey('people.StudentProfile', on_delete=models.CASCADE)
    recommended_class = models.ForeignKey('academic.AcademicClass', on_delete=models.CASCADE)
    decision = models.CharField(max_length=30, default='promoted')  # promoted, retained, conditional

    def __str__(self):
        return f"{self.student.student_number} -> {self.decision}"


class AcademicRecord(TenantBaseModel):
    """
    Flat cached records that transcript generator modules can load without recalc loops.
    """
    student = models.ForeignKey('people.StudentProfile', on_delete=models.CASCADE)
    subject = models.ForeignKey('academic.Subject', on_delete=models.CASCADE)
    cumulative_average = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.student.student_number} subject average: {self.cumulative_average}%"


class CumulativeRecord(TenantBaseModel):
    student = models.ForeignKey('people.StudentProfile', on_delete=models.CASCADE)
    cgpa = models.DecimalField(max_digits=4, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.student.student_number} CGPA: {self.cgpa}"


class ReportTemplate(TenantBaseModel):
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE)
    template_name = models.CharField(max_length=150)

    def __str__(self):
        return self.template_name
