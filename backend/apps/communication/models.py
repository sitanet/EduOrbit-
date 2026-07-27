import uuid
from django.db import models
from django.utils import timezone
from backend.apps.core.models import TenantBaseModel, PlatformBaseModel

# ==============================================================
# ANNOUNCEMENTS & GENERAL NOTIFICATIONS
# ==============================================================

class Announcement(TenantBaseModel):
    """
    Platform, school, or class-level announcements with visibility filters.
    """
    PRIORITY_CHOICES = [
        ('emergency', 'Emergency'),
        ('academic', 'Academic'),
        ('finance', 'Finance'),
        ('general', 'General')
    ]
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content = models.TextField()
    priority = models.CharField(max_length=30, choices=PRIORITY_CHOICES, default='general')
    visibility = models.CharField(max_length=50, default='all')  # all, teachers, parents, students
    publish_at = models.DateTimeField(default=timezone.now)
    requires_acknowledgement = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class Notification(TenantBaseModel):
    """
    Universal notification log mapping individual message queues.
    """
    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed')
    ]
    recipient = models.ForeignKey('people.Person', on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=150)
    message = models.TextField()
    delivery_channel = models.CharField(max_length=30, default='in_app')  # email, sms, push, whatsapp, in_app
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')
    read_status = models.BooleanField(default=False)
    delivered_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.title} to {self.recipient.person_number}"


class NotificationPreference(TenantBaseModel):
    """
    Allows users to toggle opt-in settings for specific alerts categories.
    """
    user = models.ForeignKey('identity.User', on_delete=models.CASCADE, related_name='preferences')
    category = models.CharField(max_length=50)  # e.g., fees, results, attendance
    email_enabled = models.BooleanField(default=True)
    sms_enabled = models.BooleanField(default=False)
    push_enabled = models.BooleanField(default=True)
    whatsapp_enabled = models.BooleanField(default=False)

    def __str__(self):
        return f"Prefs for {self.user.username} (Category: {self.category})"


# ==============================================================
# CAMPAIGNS & REUSABLE TEMPLATES
# ==============================================================

class NotificationTemplate(TenantBaseModel):
    name = models.CharField(max_length=100, unique=True)
    subject_template = models.CharField(max_length=255)
    body_template = models.TextField()

    def __str__(self):
        return self.name


class BroadcastCampaign(TenantBaseModel):
    name = models.CharField(max_length=150)
    target_audience = models.CharField(max_length=100)  # all, teachers, debtors
    sent_count = models.IntegerField(default=0)
    delivered_count = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class CampaignAnalytics(TenantBaseModel):
    campaign = models.ForeignKey(BroadcastCampaign, on_delete=models.CASCADE, related_name='analytics')
    open_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    click_through_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Analytics for {self.campaign.name}"


# ==============================================================
# MESSAGING CHATS & COLLABORATIVE BOARDS
# ==============================================================

class Conversation(TenantBaseModel):
    participants = models.ManyToManyField('people.Person', related_name='conversations')

    def __str__(self):
        return f"Conversation: {self.id}"


class Message(TenantBaseModel):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey('people.Person', on_delete=models.CASCADE)
    text = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Msg from {self.sender.person_number}: {self.text[:30]}"


class DiscussionBoard(TenantBaseModel):
    name = models.CharField(max_length=150)
    category = models.CharField(max_length=50)  # pta, subject, alumni

    def __str__(self):
        return self.name


# ==============================================================
# EVENTS, RSVP, SURVEYS & IMMUTABLE LOGS
# ==============================================================

class Event(TenantBaseModel):
    title = models.CharField(max_length=150)
    start_time = models.DateTimeField(default=timezone.now)
    resource = models.ForeignKey('academic.AcademicResource', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.title


class EventRegistration(TenantBaseModel):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    person = models.ForeignKey('people.Person', on_delete=models.CASCADE)
    status = models.CharField(max_length=30, default='attending')  # attending, maybe, declined

    def __str__(self):
        return f"{self.person.person_number} RSVP in {self.event.title} ({self.status})"


class Survey(TenantBaseModel):
    title = models.CharField(max_length=150)
    question = models.TextField()

    def __str__(self):
        return self.title


class CommunicationLog(TenantBaseModel):
    """
    Immutable transaction logs tracking delivery reports.
    """
    sender_identity = models.CharField(max_length=150)
    recipient_identity = models.CharField(max_length=150)
    channel = models.CharField(max_length=30)
    status = models.CharField(max_length=30)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Log: {self.channel} -> {self.status} on {self.created_at}"


# ==============================================================
# HELPDESK & CRM SUPPORT TICKETS
# ==============================================================

class SupportTicket(TenantBaseModel):
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE)
    requester = models.ForeignKey('people.Person', on_delete=models.CASCADE, related_name='support_tickets')
    subject = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50, default='general')  # academic, finance, technical, portal
    priority = models.CharField(max_length=20, default='medium')  # low, medium, high, urgent
    status = models.CharField(max_length=20, default='open')  # open, in_progress, resolved, closed
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Ticket #{self.id}: {self.subject} ({self.status})"

