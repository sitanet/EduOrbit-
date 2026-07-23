import uuid
from django.db import models
from django.utils import timezone
from backend.apps.core.models import TenantBaseModel, PlatformBaseModel

# ==============================================================
# CURRICULUM & LAYERS OF PLANNING
# ==============================================================

class Curriculum(PlatformBaseModel):
    """
    Global Curriculum structure (e.g. Cambridge IGCSE 2026, Nigerian Curriculum).
    """
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=50, unique=True)
    version = models.CharField(max_length=20, default='1.0')

    def __str__(self):
        return f"{self.name} v{self.version}"


class SchemeOfWork(TenantBaseModel):
    """
    Termly or annual Scheme of Work scoped per School.
    """
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE)
    curriculum = models.ForeignKey(Curriculum, on_delete=models.CASCADE)
    academic_year = models.ForeignKey('academic.AcademicYear', on_delete=models.CASCADE)
    academic_period = models.ForeignKey('academic.AcademicPeriod', on_delete=models.CASCADE)
    subject = models.ForeignKey('academic.Subject', on_delete=models.CASCADE)
    target_level = models.ForeignKey('academic.AcademicLevel', on_delete=models.CASCADE)

    def __str__(self):
        return f"Scheme: {self.subject.name} - {self.target_level.name}"


class WeeklyPlan(TenantBaseModel):
    scheme = models.ForeignKey(SchemeOfWork, on_delete=models.CASCADE, related_name='weekly_plans')
    week_number = models.IntegerField()
    topics_covered = models.TextField()

    def __str__(self):
        return f"Week {self.week_number} Plan for {self.scheme}"


class LessonPlan(TenantBaseModel):
    """
    Daily or single-lesson plans versioned.
    """
    weekly_plan = models.ForeignKey(WeeklyPlan, on_delete=models.CASCADE, related_name='lesson_plans')
    title = models.CharField(max_length=150)
    objectives_summary = models.TextField()
    activities_description = models.TextField()
    version_number = models.IntegerField(default=1)

    def __str__(self):
        return f"Plan: {self.title} (v{self.version_number})"


# ==============================================================
# LESSON INSTANCE & DELIVERY STATUSES
# ==============================================================

class LessonInstance(TenantBaseModel):
    """
    Today's actual classroom delivery slot mapping a scheduled timetable slot.
    """
    schedule = models.ForeignKey('timetable.Schedule', on_delete=models.CASCADE, related_name='instances')
    lesson_plan = models.ForeignKey(LessonPlan, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"Instance for {self.schedule} on {self.date}"


class LessonDelivery(TenantBaseModel):
    """
    Delivery status tracker (planned, started, completed, cancelled, rescheduled).
    """
    lesson_instance = models.OneToOneField(LessonInstance, on_delete=models.CASCADE, related_name='delivery')
    status = models.CharField(max_length=30, default='planned')  # planned, started, completed, cancelled
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Delivery Status: {self.status}"


# ==============================================================
# LEARNING OBJECTIVES & RESOURCES
# ==============================================================

class LearningObjective(TenantBaseModel):
    subject = models.ForeignKey('academic.Subject', on_delete=models.CASCADE)
    code = models.CharField(max_length=50)
    description = models.TextField()
    taxonomy_level = models.CharField(max_length=50, default='understanding')  # Bloom's level

    def __str__(self):
        return f"{self.code}: {self.description[:40]}..."


class ResourceCategory(PlatformBaseModel):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class TeachingResource(TenantBaseModel):
    """
    Teacher assets mapped by department or private sharing scope.
    """
    category = models.ForeignKey(ResourceCategory, on_delete=models.CASCADE)
    name = models.CharField(max_length=150)
    scope = models.CharField(max_length=30, default='personal')  # personal, department, school

    def __str__(self):
        return self.name


class TeachingResourceVersion(TenantBaseModel):
    resource = models.ForeignKey(TeachingResource, on_delete=models.CASCADE, related_name='versions')
    version_number = models.IntegerField(default=1)
    file_path = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.resource.name} v{self.version_number}"


# ==============================================================
# ASSIGNMENTS, OBSERVATIONS, & JOURNALS
# ==============================================================

class Assignment(TenantBaseModel):
    """
    Homework, classwork, and project headers.
    """
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE)
    teacher = models.ForeignKey('people.Person', on_delete=models.CASCADE)
    academic_class = models.ForeignKey('academic.AcademicClass', on_delete=models.CASCADE)
    subject = models.ForeignKey('academic.Subject', on_delete=models.CASCADE)
    title = models.CharField(max_length=150)
    content = models.TextField()
    assignment_type = models.CharField(max_length=30, default='homework')  # homework, classwork, project

    def __str__(self):
        return f"{self.title} ({self.assignment_type})"


class StudentObservation(TenantBaseModel):
    """
    Observations recorded by teachers feeding into student timelines.
    """
    student = models.ForeignKey('people.StudentProfile', on_delete=models.CASCADE)
    teacher = models.ForeignKey('people.Person', on_delete=models.CASCADE)
    category = models.CharField(max_length=30, default='academic')  # academic, behavior, welfare
    content = models.TextField()
    visibility = models.CharField(max_length=30, default='staff_only')  # public, staff_only, management_only

    def __str__(self):
        return f"Obs on {self.student.student_number} by {self.teacher.last_name}"


class TeachingJournal(TenantBaseModel):
    teacher = models.ForeignKey('people.Person', on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    lessons_delivered = models.IntegerField(default=0)
    topics_covered = models.TextField()
    challenges = models.TextField(blank=True)
    reflection = models.TextField(blank=True)

    def __str__(self):
        return f"Journal for {self.teacher.last_name} on {self.date}"


class TeachingAnalytics(TenantBaseModel):
    teacher = models.ForeignKey('people.Person', on_delete=models.CASCADE)
    academic_year = models.ForeignKey('academic.AcademicYear', on_delete=models.CASCADE)
    lessons_planned = models.IntegerField(default=0)
    lessons_delivered = models.IntegerField(default=0)
    homework_issued = models.IntegerField(default=0)

    def __str__(self):
        return f"Analytics: {self.teacher.last_name}"
