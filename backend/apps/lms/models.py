import uuid
from django.db import models
from django.utils import timezone
from backend.apps.core.models import TenantBaseModel, PlatformBaseModel

# ==============================================================
# CONTENT TYPES & PLANNING HEADERS
# ==============================================================

class ContentType(PlatformBaseModel):
    """
    Lookups for content formats (PDF, DOCX, SCORM, video, rich text).
    """
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)  # e.g., 'pdf', 'scorm'

    def __str__(self):
        return self.name


class LearningModule(TenantBaseModel):
    """
    Subject modules (e.g. Algebra I).
    """
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE)
    subject = models.ForeignKey('academic.Subject', on_delete=models.CASCADE)
    topic = models.CharField(max_length=150)
    title = models.CharField(max_length=150)
    version = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.title} (Subject: {self.subject.name})"


class LearningUnit(TenantBaseModel):
    """
    Units inside a Module (e.g., Quadratic Equations).
    """
    module = models.ForeignKey(LearningModule, on_delete=models.CASCADE, related_name='units')
    name = models.CharField(max_length=150)
    order = models.IntegerField(default=1)

    def __str__(self):
        return f"Unit: {self.name} ({self.module.title})"


# ==============================================================
# REUSABLE DIGITAL LIBRARY RESOURCE
# ==============================================================

class DigitalLibraryResource(TenantBaseModel):
    """
    Unified central digital asset vault reusable across LMS, Library, and Portals.
    """
    VISIBILITY = [
        ('platform', 'Platform Wide'),
        ('tenant', 'Tenant Group Wide'),
        ('school', 'School Wide'),
        ('department', 'Department Wide'),
        ('personal', 'Private Personal')
    ]
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    file_path = models.CharField(max_length=255)
    category = models.CharField(max_length=50, default='pdf')  # ebook, worksheet, video, policy
    visibility = models.CharField(max_length=30, choices=VISIBILITY, default='school')
    tags_metadata = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.title


# ==============================================================
# CONTENT VERSIONING & DRM
# ==============================================================

class LearningContent(TenantBaseModel):
    """
    Study items mapped under a Unit.
    """
    unit = models.ForeignKey(LearningUnit, on_delete=models.CASCADE, related_name='contents')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    title = models.CharField(max_length=150)
    library_resource = models.ForeignKey(DigitalLibraryResource, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.title} ({self.content_type.name})"


class LearningContentVersion(TenantBaseModel):
    content = models.ForeignKey(LearningContent, on_delete=models.CASCADE, related_name='versions')
    version_number = models.IntegerField(default=1)
    body = models.TextField(blank=True)
    file_path = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, default='draft')  # draft, published, archived
    
    # Accessibility captions / screen reader tracks
    accessibility_metadata = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.content.title} v{self.version_number} ({self.status})"


class ContentLicense(TenantBaseModel):
    """
    Digital Rights Management parameters restricting downloads.
    """
    content = models.OneToOneField(LearningContent, on_delete=models.CASCADE, related_name='license')
    downloadable = models.BooleanField(default=True)
    stream_only = models.BooleanField(default=False)
    expiry_date = models.DateField(null=True, blank=True)
    device_limit = models.IntegerField(default=3)
    printing_permission = models.BooleanField(default=False)

    def __str__(self):
        return f"DRM: {self.content.title}"


# ==============================================================
# ACTIVITIES & SEQUENCING PATHS
# ==============================================================

class LearningActivity(TenantBaseModel):
    """
    Actions (reading files, video plays, assignments tasks).
    """
    unit = models.ForeignKey(LearningUnit, on_delete=models.CASCADE, related_name='activities')
    name = models.CharField(max_length=150)
    activity_type = models.CharField(max_length=30)  # reading, video, assignment
    
    learning_objective = models.ForeignKey('teachers.LearningObjective', on_delete=models.SET_NULL, null=True, blank=True)
    content = models.ForeignKey(LearningContent, on_delete=models.SET_NULL, null=True, blank=True)
    assignment = models.ForeignKey('teachers.Assignment', on_delete=models.SET_NULL, null=True, blank=True)
    order = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.name} ({self.activity_type})"


class LearningPath(TenantBaseModel):
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE)
    name = models.CharField(max_length=150)

    def __str__(self):
        return self.name


class LearningPathStep(TenantBaseModel):
    path = models.ForeignKey(LearningPath, on_delete=models.CASCADE, related_name='steps')
    module = models.ForeignKey(LearningModule, on_delete=models.CASCADE)
    prerequisite = models.ForeignKey(LearningModule, on_delete=models.SET_NULL, null=True, blank=True, related_name='next_steps')
    order = models.IntegerField(default=1)

    def __str__(self):
        return f"Step {self.order} for {self.path.name}"


# ==============================================================
# PROGRESS & GAMIFICATION
# ==============================================================

class StudentProgress(TenantBaseModel):
    """
    Progress records tracking completions.
    """
    student = models.ForeignKey('people.StudentProfile', on_delete=models.CASCADE)
    activity = models.ForeignKey(LearningActivity, on_delete=models.CASCADE)
    status = models.CharField(max_length=30, default='started')  # started, in_progress, completed
    first_access = models.DateTimeField(default=timezone.now)
    last_access = models.DateTimeField(default=timezone.now)
    completion_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    total_time_seconds = models.IntegerField(default=0)
    
    # Advanced metrics tracking
    active_time_seconds = models.IntegerField(default=0)
    pause_count = models.IntegerField(default=0)
    resume_count = models.IntegerField(default=0)
    offline_sync_status = models.CharField(max_length=30, default='synced')  # pending, synced, conflict
    last_device = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"{self.student.student_number} -> {self.activity.name} ({self.status})"


class Badge(PlatformBaseModel):
    name = models.CharField(max_length=100)
    description = models.TextField()
    image_url = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.name


class Achievement(PlatformBaseModel):
    name = models.CharField(max_length=100)
    description = models.TextField()
    points_rewarded = models.IntegerField(default=10)

    def __str__(self):
        return self.name


class StudentBadge(TenantBaseModel):
    student = models.ForeignKey('people.StudentProfile', on_delete=models.CASCADE)
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    date_earned = models.DateField(default=timezone.now)

    def __str__(self):
        return f"{self.student.student_number} earned {self.badge.name}"


class StudentPoints(TenantBaseModel):
    student = models.ForeignKey('people.StudentProfile', on_delete=models.CASCADE, related_name='points_ledgers')
    points = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.student.student_number} ({self.points} pts)"


# ==============================================================
# DISCUSSIONS & ANNOUNCEMENTS
# ==============================================================

class Discussion(TenantBaseModel):
    unit = models.ForeignKey(LearningUnit, on_delete=models.CASCADE, related_name='discussions')
    title = models.CharField(max_length=150)

    def __str__(self):
        return self.title


class Thread(TenantBaseModel):
    discussion = models.ForeignKey(Discussion, on_delete=models.CASCADE, related_name='threads')
    author = models.ForeignKey('people.Person', on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Thread by {self.author.last_name}"


class Reply(TenantBaseModel):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name='replies')
    author = models.ForeignKey('people.Person', on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Reply by {self.author.last_name}"


class LMSAnnouncement(TenantBaseModel):
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE)
    title = models.CharField(max_length=150)
    content = models.TextField()
    target_scope = models.CharField(max_length=30, default='school')  # school, class, subject

    def __str__(self):
        return self.title


# ==============================================================
# OFFLINE LEARNING PACKAGES & SEARCH ENGINE
# ==============================================================

class OfflinePackage(TenantBaseModel):
    """
    Downloadable course archives for offline operations.
    """
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE)
    name = models.CharField(max_length=150)
    zip_file_path = models.CharField(max_length=255)
    version = models.IntegerField(default=1)

    def __str__(self):
        return f"Offline: {self.name} v{self.version}"


class OfflineManifest(TenantBaseModel):
    package = models.ForeignKey(OfflinePackage, on_delete=models.CASCADE, related_name='manifests')
    resource_path = models.CharField(max_length=255)
    file_hash = models.CharField(max_length=64)

    def __str__(self):
        return self.resource_path


class LearningSearchIndex(TenantBaseModel):
    """
    Dedicated index table caching search terms mappings.
    """
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE)
    search_keywords = models.TextField()
    subject_code = models.CharField(max_length=50)
    topic = models.CharField(max_length=150)
    content_id = models.UUIDField()

    def __str__(self):
        return f"Search Index: {self.topic}"
