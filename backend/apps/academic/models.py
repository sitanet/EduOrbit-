import uuid
from django.db import models
from django.utils import timezone
from backend.apps.core.models import TenantBaseModel, PlatformBaseModel

# ==============================================================
# GLOBAL ACADEMIC BLUEPRINTS (PLATFORM SCOPED)
# ==============================================================

class Curriculum(PlatformBaseModel):
    """
    Global Curriculum reference definitions supporting versioning.
    (e.g., Nigerian 2014, Cambridge IGCSE 2024, IB Primary Years).
    """
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=50, unique=True, db_index=True)  # e.g. 'cambridge-igcse-2024'
    version = models.CharField(max_length=20, default='1.0.0')
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = "Curriculum"
        verbose_name_plural = "Curricula"

    def __str__(self):
        return f"{self.name} v{self.version}"


# ==============================================================
# SCHOOL LEVEL ACADEMIC CONFIGURATIONS (SCHOOL SCOPED)
# ==============================================================

class AcademicSettings(TenantBaseModel):
    """
    School-wide default academic settings.
    """
    school = models.OneToOneField('tenants.School', on_delete=models.CASCADE, related_name='academic_settings')
    working_days = models.JSONField(default=list, help_text="e.g. ['monday', 'tuesday', 'wednesday']")
    periods_per_day = models.IntegerField(default=8)
    passing_mark = models.DecimalField(max_digits=5, decimal_places=2, default=50.0)
    max_subjects_per_student = models.IntegerField(default=15)
    weekend_teaching = models.BooleanField(default=False)

    def __str__(self):
        return f"Settings for {self.school.name}"


class AcademicYear(TenantBaseModel):
    """
    School Academic Year cycles (e.g. 2026/2027).
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('future', 'Future'),
        ('archived', 'Archived')
    ]
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE, related_name='academic_years')
    name = models.CharField(max_length=100)  # e.g. 2026/2027
    code = models.CharField(max_length=20, db_index=True)  # e.g. 2026-2027
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='future')

    class Meta:
        unique_together = ('school', 'code')
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.name} ({self.school.name})"


class AcademicPeriod(TenantBaseModel):
    """
    Academic periods (Terms, Semesters, Quarters) under an Academic Year.
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('future', 'Future')
    ]
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='periods')
    name = models.CharField(max_length=100)  # e.g. Term 1, Semester 1
    order = models.IntegerField(default=1)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='future')

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.name} - {self.academic_year.name}"


# ==============================================================
# HIERARCHICAL LEVELS & CLASSES
# ==============================================================

class EducationLevel(TenantBaseModel):
    """
    Education Levels (e.g. Nursery, Primary, Senior Secondary).
    """
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE, related_name='education_levels')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50)  # e.g. 'primary', 'nursery'
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('school', 'code')

    def __str__(self):
        return f"{self.name} ({self.school.name})"


class Department(TenantBaseModel):
    """
    School administrative/academic departments (e.g., Science, Commercial, Arts).
    """
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE, related_name='departments')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50)

    class Meta:
        unique_together = ('school', 'code')

    def __str__(self):
        return f"{self.name} ({self.school.name})"


class AcademicLevel(TenantBaseModel):
    """
    Academic Level (e.g. Primary 1, JSS 1, Grade 10).
    """
    education_level = models.ForeignKey(EducationLevel, on_delete=models.CASCADE, related_name='levels')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50)  # e.g. 'primary-1', 'grade-10'

    class Meta:
        unique_together = ('education_level', 'code')

    def __str__(self):
        return self.name


class AcademicClass(TenantBaseModel):
    """
    Academic Class representing a classroom instances (e.g., Primary 1 Gold).
    """
    academic_level = models.ForeignKey(AcademicLevel, on_delete=models.CASCADE, related_name='classes')
    name = models.CharField(max_length=100)  # e.g. Primary 1 Gold, Primary 1 Silver
    capacity = models.IntegerField(default=35)
    display_order = models.IntegerField(default=1)
    color_code = models.CharField(max_length=7, default='#2E7D32')

    def __str__(self):
        return self.name


# ==============================================================
# SUBJECTS & OFFERINGS
# ==============================================================

class SubjectCategory(TenantBaseModel):
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE, related_name='subject_categories')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50)

    class Meta:
        unique_together = ('school', 'code')

    def __str__(self):
        return f"{self.name} ({self.school.name})"


class Subject(TenantBaseModel):
    CATEGORIES = [
        ('core', 'Core'),
        ('elective', 'Elective'),
        ('language', 'Language'),
        ('stem', 'STEM'),
        ('arts', 'Arts'),
        ('commercial', 'Commercial')
    ]
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE, related_name='subjects')
    curriculum = models.ForeignKey(Curriculum, on_delete=models.CASCADE, related_name='subjects')
    code = models.CharField(max_length=50)  # e.g. 'maths-p1'
    name = models.CharField(max_length=150)
    category = models.CharField(max_length=50, default='core')
    credit_units = models.IntegerField(default=1)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('school', 'code')

    def __str__(self):
        return f"{self.name} ({self.curriculum.name})"


class SubjectOffering(TenantBaseModel):
    """
    Active Subject Offered to a specific Class during an academic year.
    """
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='offerings')
    academic_class = models.ForeignKey(AcademicClass, on_delete=models.CASCADE, related_name='offerings')
    compulsory = models.BooleanField(default=True)
    teacher_user_id = models.UUIDField(null=True, blank=True)

    def __str__(self):
        return f"{self.subject.name} in {self.academic_class.name}"


# ==============================================================
# GRADING, ASSESSMENT, & PROMOTION SCHEMES
# ==============================================================

class GradingScale(TenantBaseModel):
    """
    Custom grading boundaries configurations (Percents or GPA mappings).
    """
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE, related_name='grading_scales')
    education_level = models.ForeignKey(EducationLevel, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=50)  # e.g., 'Grade A'
    min_score = models.DecimalField(max_digits=5, decimal_places=2)  # e.g., 80.0
    max_score = models.DecimalField(max_digits=5, decimal_places=2)  # e.g., 100.0
    grade_letter = models.CharField(max_length=5)  # e.g., 'A+'
    gpa_value = models.DecimalField(max_digits=4, decimal_places=2, default=4.0)
    remarks = models.CharField(max_length=150, blank=True)

    def __str__(self):
        return f"{self.grade_letter} ({self.min_score}% - {self.max_score}%)"


class AssessmentComponent(TenantBaseModel):
    """
    Weighted academic evaluation components (Quiz, CA, Exam).
    """
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE, related_name='assessment_components')
    education_level = models.ForeignKey(EducationLevel, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)  # e.g. Class Assignment, Final Exam
    max_score = models.IntegerField(default=100)
    weight_percentage = models.DecimalField(max_digits=5, decimal_places=2)  # e.g. 60.0%
    sequence = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.name} ({self.weight_percentage}%)"


class PromotionPolicy(TenantBaseModel):
    """
    Weighted rules governing automatic student promotion requirements.
    """
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE, related_name='promotion_policies')
    academic_level = models.ForeignKey(AcademicLevel, on_delete=models.CASCADE)
    
    minimum_overall_score = models.DecimalField(max_digits=5, decimal_places=2, default=50.0)
    minimum_subject_passes = models.IntegerField(default=5)
    attendance_percentage_required = models.DecimalField(max_digits=5, decimal_places=2, default=75.0)
    manual_override_allowed = models.BooleanField(default=True)

    def __str__(self):
        return f"Promotion rules - {self.academic_level.name}"


# ==============================================================
# CALENDAR EVENTS & TIMETABLE RESOURCES
# ==============================================================

class SchoolCalendarEvent(TenantBaseModel):
    """
    School activities calendar schedules supporting recurring rules.
    """
    EVENT_CATEGORIES = [
        ('holiday', 'Holiday'),
        ('examination', 'Examination'),
        ('pta', 'PTA Meeting'),
        ('sports', 'Sports Event'),
        ('closure', 'School Closure')
    ]
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE, related_name='calendar_events')
    title = models.CharField(max_length=150)
    category = models.CharField(max_length=30, choices=EVENT_CATEGORIES, default='holiday')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    recurrence_rule = models.JSONField(default=dict, blank=True, help_text="e.g. {'frequency': 'yearly', 'month': 10}")

    def __str__(self):
        return self.title


class AcademicResource(TenantBaseModel):
    """
    Timetabling resources profiles (Rooms, Laboratories, Halls).
    """
    TYPES = [
        ('room', 'Classroom'),
        ('lab', 'Laboratory'),
        ('hall', 'Auditorium Hall'),
        ('sports', 'Sports Facility')
    ]
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE, related_name='academic_resources')
    name = models.CharField(max_length=100)
    resource_type = models.CharField(max_length=30, choices=TYPES, default='room')
    capacity = models.IntegerField(default=40)

    def __str__(self):
        return f"{self.name} ({self.resource_type})"

