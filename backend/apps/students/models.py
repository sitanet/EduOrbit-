import uuid
from django.db import models
from django.utils import timezone
from backend.apps.core.models import TenantBaseModel
from backend.apps.core.state_machine import StateMachine, InvalidStateTransitionError

# ==============================================================
# STATE MACHINE TRANSITIONS DEF
# ==============================================================

STUDENT_LIFECYCLE_TRANSITIONS = {
    'pending': ['active', 'archived'],
    'active': ['suspended', 'withdrawn', 'expelled', 'graduated', 'archived'],
    'suspended': ['active', 'withdrawn', 'expelled', 'archived'],
    'withdrawn': ['active', 'archived'],
    'expelled': ['archived'],
    'graduated': ['alumni', 'archived'],
    'alumni': ['archived'],
    'archived': []
}

student_state_machine = StateMachine(
    transitions=STUDENT_LIFECYCLE_TRANSITIONS,
    initial_state='pending'
)


# ==============================================================
# HOUSES & CLUBS MODELS
# ==============================================================

class SchoolHouse(TenantBaseModel):
    """
    School boarding or competitive houses (e.g. Red House).
    """
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE, related_name='houses')
    name = models.CharField(max_length=100)
    color_code = models.CharField(max_length=7, default='#d32f2f')
    house_master_id = models.UUIDField(null=True, blank=True)
    house_captain_id = models.UUIDField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.school.name})"


class StudentClub(TenantBaseModel):
    """
    School extracurricular clubs (e.g. Robotics, Press Club).
    """
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE, related_name='clubs')
    name = models.CharField(max_length=100)
    supervisor_user_id = models.UUIDField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.school.name})"


class StudentClubMembership(TenantBaseModel):
    student = models.ForeignKey('people.StudentProfile', on_delete=models.CASCADE, related_name='club_memberships')
    club = models.ForeignKey(StudentClub, on_delete=models.CASCADE, related_name='members')
    joined_date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"{self.student.student_number} in {self.club.name}"


# ==============================================================
# LIFECYCLE ENGINE STATUS & TAGS
# ==============================================================

class StudentStatusHistory(TenantBaseModel):
    """
    Chronological historical logs of student status changes validating using state machines.
    """
    student = models.ForeignKey('people.StudentProfile', on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField(max_length=30)
    effective_date = models.DateTimeField(default=timezone.now)
    reason = models.TextField(blank=True)

    class Meta:
        ordering = ['-effective_date']

    def __str__(self):
        return f"{self.student.student_number} -> {self.status}"


class StudentTag(TenantBaseModel):
    """
    Dynamic taxonomy tags (e.g., Scholarship, Athlete).
    """
    student = models.ForeignKey('people.StudentProfile', on_delete=models.CASCADE, related_name='tags')
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


# ==============================================================
# PLACEMENTS & PROMOTIONS
# ==============================================================

class AcademicPlacementHistory(TenantBaseModel):
    """
    Tracks historical placements. NEVER overwritten.
    """
    student = models.ForeignKey('people.StudentProfile', on_delete=models.CASCADE, related_name='placements')
    academic_year = models.ForeignKey('academic.AcademicYear', on_delete=models.CASCADE)
    academic_class = models.ForeignKey('academic.AcademicClass', on_delete=models.CASCADE)
    house = models.ForeignKey(SchoolHouse, on_delete=models.SET_NULL, null=True, blank=True)
    campus = models.ForeignKey('tenants.Campus', on_delete=models.SET_NULL, null=True, blank=True)
    effective_date = models.DateField(default=timezone.now)

    class Meta:
        ordering = ['-effective_date']

    def __str__(self):
        return f"{self.student.student_number} @ {self.academic_class.name}"


class ClassPromotion(TenantBaseModel):
    """
    Promotions logs tracking moving students across classes.
    """
    student = models.ForeignKey('people.StudentProfile', on_delete=models.CASCADE)
    previous_class = models.ForeignKey('academic.AcademicClass', on_delete=models.CASCADE, related_name='promotions_out')
    new_class = models.ForeignKey('academic.AcademicClass', on_delete=models.CASCADE, related_name='promotions_in')
    effective_date = models.DateField(default=timezone.now)
    promotion_type = models.CharField(max_length=30, default='automatic')  # automatic, manual, conditional
    reason = models.TextField(blank=True)

    def __str__(self):
        return f"Promo {self.student.student_number} to {self.new_class.name}"


# ==============================================================
# TRANSFERS & DISCIPLINE
# ==============================================================

class StudentTransfer(TenantBaseModel):
    student = models.ForeignKey('people.StudentProfile', on_delete=models.CASCADE)
    previous_school = models.ForeignKey('tenants.School', on_delete=models.CASCADE, related_name='transfers_out')
    new_school = models.ForeignKey('tenants.School', on_delete=models.CASCADE, related_name='transfers_in')
    effective_date = models.DateField(default=timezone.now)
    reason = models.TextField()

    def __str__(self):
        return f"Transfer {self.student.student_number} to {self.new_school.name}"


class StudentDiscipline(TenantBaseModel):
    student = models.ForeignKey('people.StudentProfile', on_delete=models.CASCADE, related_name='discipline_records')
    record_type = models.CharField(max_length=30)  # merit, demerit, warning
    points = models.IntegerField(default=0)
    reason = models.TextField()
    recorded_date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"{self.record_type} ({self.points}) for {self.student.student_number}"


# ==============================================================
# PORTFOLIOS, TIMELINES, & NOTES
# ==============================================================

class StudentPortfolio(TenantBaseModel):
    student = models.ForeignKey('people.StudentProfile', on_delete=models.CASCADE, related_name='portfolio_records')
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    date_earned = models.DateField()

    def __str__(self):
        return self.title


class StudentTimeline(TenantBaseModel):
    """
    Central chronological log of every student life event.
    """
    student = models.ForeignKey('people.StudentProfile', on_delete=models.CASCADE, related_name='timeline')
    event_type = models.CharField(max_length=50)  # admitted, promoted, joined_club
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    occurred_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-occurred_at']

    def __str__(self):
        return f"{self.event_type} - {self.title}"


class StudentNote(TenantBaseModel):
    PRIVACY_LEVELS = [
        ('public', 'Public'),
        ('staff_only', 'Staff Only'),
        ('management_only', 'Management Only')
    ]
    student = models.ForeignKey('people.StudentProfile', on_delete=models.CASCADE, related_name='notes')
    note_type = models.CharField(max_length=30)  # academic, behavior, welfare
    content = models.TextField()
    privacy_level = models.CharField(max_length=30, choices=PRIVACY_LEVELS, default='staff_only')
    author_user_id = models.UUIDField()
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Note on {self.student.student_number} by {self.author_user_id}"
