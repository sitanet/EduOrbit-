import uuid
from django.db import models
from django.utils import timezone
from backend.apps.core.models import TenantBaseModel, PlatformBaseModel

# ==============================================================
# QUESTION BANK & MEDIA METADATA
# ==============================================================

class Question(TenantBaseModel):
    """
    Reusable question item containing core statement details.
    """
    TYPES = [
        ('mcq', 'Multiple Choice'),
        ('true_false', 'True/False'),
        ('matching', 'Matching'),
        ('essay', 'Essay')
    ]
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE)
    subject = models.ForeignKey('academic.Subject', on_delete=models.CASCADE)
    topic = models.CharField(max_length=150)
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=TYPES, default='mcq')
    
    complexity = models.CharField(max_length=20, default='medium')  # easy, medium, hard
    default_marks = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)
    version = models.IntegerField(default=1)
    status = models.CharField(max_length=20, default='published')  # draft, published, archived

    def __str__(self):
        return f"{self.question_text[:50]}... ({self.question_type})"


class QuestionChoice(TenantBaseModel):
    """
    Options answers mapping to a Multiple Choice / True-False question.
    """
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    choice_text = models.TextField()
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.choice_text[:30]


class QuestionMedia(TenantBaseModel):
    """
    Linked diagram, sound recording, or video instructions.
    """
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='media')
    file_path = models.CharField(max_length=255)
    media_type = models.CharField(max_length=30)  # image, audio, video

    def __str__(self):
        return f"{self.media_type}: {self.file_path}"


# ==============================================================
# BLUEPRINTS, SCHEDULING, & SECTIONS
# ==============================================================

class AssessmentBlueprint(TenantBaseModel):
    """
    Rules criteria selecting questions dynamically from pools.
    """
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE)
    subject = models.ForeignKey('academic.Subject', on_delete=models.CASCADE)
    number_of_questions = models.IntegerField(default=10)
    topics = models.JSONField(default=list, blank=True)
    difficulty_distribution = models.JSONField(default=dict, blank=True)  # {"easy": 4, "medium": 6}

    def __str__(self):
        return f"Blueprint: {self.subject.name} ({self.number_of_questions} Qs)"


class Assessment(TenantBaseModel):
    """
    The actual assessment header (quizzes, final exams).
    """
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE)
    blueprint = models.ForeignKey(AssessmentBlueprint, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=150)
    duration_minutes = models.IntegerField(default=60)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class AssessmentSection(TenantBaseModel):
    """
    Segment blocks dividing exams (e.g. Section A, Section B).
    """
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='sections')
    name = models.CharField(max_length=100)  # Section A - MCQs
    order = models.IntegerField(default=1)
    marks_weight = models.DecimalField(max_digits=5, decimal_places=2, default=100.00)

    def __str__(self):
        return f"{self.name} ({self.assessment.title})"


# ==============================================================
# ATTEMPTS & PROCTOR SECURITY
# ==============================================================

class AssessmentAttempt(TenantBaseModel):
    """
    An execution log of a student sitting an exam.
    """
    student = models.ForeignKey('people.StudentProfile', on_delete=models.CASCADE)
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE)
    status = models.CharField(max_length=30, default='started')  # started, completed, expired
    time_started = models.DateTimeField(default=timezone.now)
    time_submitted = models.DateTimeField(null=True, blank=True)
    
    # Restoring checkpoints payload
    recovery_payload = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.student.student_number} -> {self.assessment.title} ({self.status})"


class AttemptAnswer(TenantBaseModel):
    """
    Individual answers log mapping points scored.
    """
    attempt = models.ForeignKey(AssessmentAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_choice = models.ForeignKey(QuestionChoice, on_delete=models.SET_NULL, null=True, blank=True)
    text_answer = models.TextField(blank=True)
    is_correct = models.BooleanField(default=False)
    marks_earned = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Q: {self.question.id} Score: {self.marks_earned}"


class ProctorLog(TenantBaseModel):
    """
    Logs suspicious activities during CBT exams.
    """
    attempt = models.ForeignKey(AssessmentAttempt, on_delete=models.CASCADE, related_name='proctor_logs')
    event_type = models.CharField(max_length=50)  # tab_switch, copy_attempt, devtools_open
    timestamp = models.DateTimeField(default=timezone.now)
    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.event_type} on {self.timestamp}"


# ==============================================================
# RUBRICS, MODERATION, & RESULTS SUMMARY
# ==============================================================

class Rubric(TenantBaseModel):
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE)
    name = models.CharField(max_length=150)

    def __str__(self):
        return self.name


class RubricCriteria(TenantBaseModel):
    rubric = models.ForeignKey(Rubric, on_delete=models.CASCADE, related_name='criteria')
    description = models.TextField()
    max_marks = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)

    def __str__(self):
        return self.description[:40]


class AssessmentModeration(TenantBaseModel):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='moderations')
    status = models.CharField(max_length=20, default='pending')  # pending, approved, rejected
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Moderation: {self.assessment.title} ({self.status})"


class AssessmentResult(TenantBaseModel):
    """
    Cached marks statistics summary.
    """
    student = models.ForeignKey('people.StudentProfile', on_delete=models.CASCADE)
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE)
    total_score = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    grade = models.CharField(max_length=10, blank=True)

    def __str__(self):
        return f"{self.student.student_number} result: {self.percentage}%"
