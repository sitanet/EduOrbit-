import uuid
from django.db import models
from django.utils import timezone
from backend.apps.core.models import TenantBaseModel, PlatformBaseModel

# ==============================================================
# PORTAL PROFILES & CUSTOMIZATIONS
# ==============================================================

class PortalProfile(TenantBaseModel):
    user = models.OneToOneField('identity.User', on_delete=models.CASCADE, related_name='portal_profile')
    theme = models.CharField(max_length=50, default='light')
    timezone = models.CharField(max_length=100, default='UTC')

    def __str__(self):
        return f"Profile: {self.user.username}"


class PortalShortcut(TenantBaseModel):
    profile = models.ForeignKey(PortalProfile, on_delete=models.CASCADE, related_name='shortcuts')
    name = models.CharField(max_length=100)
    target_url = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class PortalAnnouncement(TenantBaseModel):
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE)
    title = models.CharField(max_length=150)
    body = models.TextField()
    target_role = models.CharField(max_length=50)  # parent, student, teacher, staff

    def __str__(self):
        return self.title


# ==============================================================
# BOOKMARKS, SESSIONS & NOTIFICATIONS
# ==============================================================

class PortalBookmark(TenantBaseModel):
    profile = models.ForeignKey(PortalProfile, on_delete=models.CASCADE, related_name='bookmarks')
    title = models.CharField(max_length=150)
    url = models.CharField(max_length=255)

    def __str__(self):
        return self.title


class PortalActivity(TenantBaseModel):
    user = models.ForeignKey('identity.User', on_delete=models.CASCADE, related_name='portal_activities')
    description = models.CharField(max_length=255)
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username} - {self.description}"


class PortalSession(TenantBaseModel):
    user = models.ForeignKey('identity.User', on_delete=models.CASCADE, related_name='portal_sessions')
    device_fingerprint = models.CharField(max_length=255)
    last_accessed = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Session: {self.user.username} on {self.device_fingerprint}"


class PortalNotification(TenantBaseModel):
    user = models.ForeignKey('identity.User', on_delete=models.CASCADE, related_name='portal_notifications')
    title = models.CharField(max_length=150)
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Notification: {self.title} to {self.user.username}"


class PortalPreference(TenantBaseModel):
    profile = models.ForeignKey(PortalProfile, on_delete=models.CASCADE, related_name='preferences')
    key = models.CharField(max_length=100)
    value = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.key} = {self.value}"


# ==============================================================
# PARENT & GUARDIAN RELATIONSHIPS
# ==============================================================

class ParentStudentRelationship(TenantBaseModel):
    parent = models.ForeignKey('people.Person', on_delete=models.CASCADE, related_name='children_relationships')
    student = models.ForeignKey('people.StudentProfile', on_delete=models.CASCADE, related_name='parent_relationships')
    relationship_type = models.CharField(max_length=50, default='father')  # father, mother, guardian
    is_emergency_contact = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.parent.last_name} ({self.relationship_type}) -> {self.student.student_number}"

