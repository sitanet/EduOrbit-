from rest_framework import serializers
from backend.apps.communication.models import (
    Announcement, Notification, NotificationPreference, NotificationTemplate, BroadcastCampaign, Message, Event, Survey, CommunicationLog
)

class AnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Announcement
        fields = ['id', 'school', 'title', 'content', 'priority', 'visibility', 'publish_at', 'requires_acknowledgement']


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'recipient', 'title', 'message', 'delivery_channel', 'status', 'read_status', 'delivered_at']


class PreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = ['id', 'user', 'category', 'email_enabled', 'sms_enabled', 'push_enabled', 'whatsapp_enabled']


class TemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationTemplate
        fields = ['id', 'name', 'subject_template', 'body_template']


class BroadcastCampaignSerializer(serializers.ModelSerializer):
    class Meta:
        model = BroadcastCampaign
        fields = ['id', 'name', 'target_audience', 'sent_count', 'delivered_count']


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'conversation', 'sender', 'text', 'is_read', 'created_at']


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ['id', 'title', 'start_time', 'resource']


class SurveySerializer(serializers.ModelSerializer):
    class Meta:
        model = Survey
        fields = ['id', 'title', 'question']


class CommunicationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunicationLog
        fields = ['id', 'sender_identity', 'recipient_identity', 'channel', 'status', 'created_at']
