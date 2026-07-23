import uuid
from django.db import models
from django.utils import timezone
from backend.apps.core.models import TenantBaseModel, PlatformBaseModel

# ==============================================================
# BELL SCHEDULES & TIME DEFINITIONS
# ==============================================================

class BellSchedule(TenantBaseModel):
    """
    Bell Schedule configs mapped per Education Level or School
    (e.g., Junior School Bell, Creche Bell).
    """
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE, related_name='bell_schedules')
    name = models.CharField(max_length=100)  # e.g., Senior Secondary Timings
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.school.name})"


class TimeSlot(TenantBaseModel):
    """
     Bell period slots nesting under a BellSchedule.
    """
    bell_schedule = models.ForeignKey(BellSchedule, on_delete=models.CASCADE, related_name='slots')
    day_of_week = models.CharField(max_length=20, choices=[
        ('monday', 'Monday'), ('tuesday', 'Tuesday'), ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'), ('friday', 'Friday'), ('saturday', 'Saturday'), ('sunday', 'Sunday')
    ])
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_break = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.day_of_week.capitalize()} {self.start_time}-{self.end_time} (Break: {self.is_break})"


# ==============================================================
# RESOURCES & TYPES
# ==============================================================

class Resource(TenantBaseModel):
    """
    Physical rooms and facilities (Classrooms, Labs, buses, halls)
    isolated per School.
    """
    TYPES = [
        ('classroom', 'Classroom'),
        ('lab', 'Laboratory'),
        ('ict', 'ICT Room'),
        ('hall', 'Auditorium Hall'),
        ('sports', 'Sports Field'),
        ('bus', 'School Bus'),
        ('clinic', 'Clinic Room'),
        ('hostel', 'Hostel Hall')
    ]
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE, related_name='timetable_resources')
    name = models.CharField(max_length=100)
    capacity = models.IntegerField(default=40)
    resource_type = models.CharField(max_length=30, choices=TYPES, default='classroom')
    status = models.CharField(max_length=30, default='available')  # available, maintenance
    availability = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.name} ({self.resource_type})"


class ScheduleType(PlatformBaseModel):
    """
    Global types of schedules (Academic Lesson, Exam, CBT, Parent Meeting).
    """
    name = models.CharField(max_length=100)  # e.g., Academic Lesson
    code = models.CharField(max_length=50, unique=True)  # e.g., 'lesson'

    def __str__(self):
        return self.name


# ==============================================================
# CORE LESSONS & SCHEDULES
# ==============================================================

class Lesson(TenantBaseModel):
    """
    Represents structural class/subject/teacher requirements
    prior to placing them into time slots.
    """
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE)
    subject = models.ForeignKey('academic.Subject', on_delete=models.CASCADE)
    teacher = models.ForeignKey('people.Person', on_delete=models.CASCADE, related_name='lessons_taught')
    academic_class = models.ForeignKey('academic.AcademicClass', on_delete=models.CASCADE, related_name='lessons')
    duration_minutes = models.IntegerField(default=40)

    def __str__(self):
        return f"{self.subject.name} - Class: {self.academic_class.name} ({self.teacher.last_name})"


class Schedule(TenantBaseModel):
    """
    Unified generic Schedule instance.
    """
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE)
    schedule_type = models.ForeignKey(ScheduleType, on_delete=models.CASCADE)
    
    # Nullable if scheduling a non-academic event
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, null=True, blank=True, related_name='schedules')
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, null=True, blank=True, related_name='schedules')
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE, null=True, blank=True, related_name='schedules')
    
    title = models.CharField(max_length=200, blank=True)  # e.g., PTA Meeting
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    
    recurrence_rule = models.JSONField(default=dict, blank=True)

    def __str__(self):
        if self.lesson:
            return f"Lesson: {self.lesson.subject.name} in {self.resource.name if self.resource else 'No Room'}"
        return f"Event: {self.title}"


# ==============================================================
# TEACHER AVAILABILITY & WORKLOADS
# ==============================================================

class TeacherAvailability(TenantBaseModel):
    """
    Off-hours or preferred teaching days.
    """
    teacher = models.OneToOneField('people.Person', on_delete=models.CASCADE, related_name='availability')
    working_days = models.JSONField(default=list)  # ['monday', 'tuesday']
    blocked_hours = models.JSONField(default=list)  # [{'start': '08:00', 'end': '10:00'}]

    def __str__(self):
        return f"Availability for {self.teacher.last_name}"


class TeacherWorkloadAnalytics(TenantBaseModel):
    """
    Tracking teacher load metrics (admin, clubs, examinations hours).
    """
    teacher = models.ForeignKey('people.Person', on_delete=models.CASCADE)
    academic_year = models.ForeignKey('academic.AcademicYear', on_delete=models.CASCADE)
    
    teaching_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    administrative_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    duties_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Workload {self.teacher.last_name} ({self.academic_year.name})"


class TeacherSubstitution(TenantBaseModel):
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name='substitutions')
    substitute_teacher = models.ForeignKey('people.Person', on_delete=models.CASCADE, related_name='substitutes')
    date = models.DateField()
    status = models.CharField(max_length=20, default='pending')  # pending, active, completed

    def __str__(self):
        return f"Sub Cover: {self.substitute_teacher.last_name} on {self.date}"


# ==============================================================
# CONSTRAINTS & CONFLICT ENGINE
# ==============================================================

class SchedulingConstraint(TenantBaseModel):
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=50, unique=True)
    constraint_type = models.CharField(max_length=50)  # max_hours, consecutive_lessons
    configuration = models.JSONField(default=dict)

    def __str__(self):
        return self.name


class SchedulingScenario(TenantBaseModel):
    name = models.CharField(max_length=100)
    status = models.CharField(max_length=20, default='draft')  # draft, active, archived

    def __str__(self):
        return self.name


class ConflictReport(TenantBaseModel):
    """
    DB registry of system-detected timetable overlaps.
    """
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE)
    conflict_type = models.CharField(max_length=50)  # teacher_clash, room_clash, class_clash
    description = models.TextField()
    severity = models.CharField(max_length=20, default='warning')  # warning, error
    
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by_user_id = models.UUIDField(null=True, blank=True)

    def __str__(self):
        return f"{self.conflict_type} ({self.severity}) - School: {self.school.name}"
