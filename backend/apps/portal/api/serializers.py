from rest_framework import serializers
from backend.apps.portal.models import (
    PortalProfile, PortalShortcut, PortalAnnouncement, PortalBookmark, PortalActivity, PortalSession, PortalNotification, PortalPreference
)

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortalProfile
        fields = ['id', 'user', 'theme', 'timezone']


class ShortcutSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortalShortcut
        fields = ['id', 'profile', 'name', 'target_url']


class AnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortalAnnouncement
        fields = ['id', 'school', 'title', 'body', 'target_role']


class BookmarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortalBookmark
        fields = ['id', 'profile', 'title', 'url']


class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = PortalActivity
        fields = ['id', 'user', 'description', 'timestamp']


class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortalSession
        fields = ['id', 'user', 'device_fingerprint', 'last_accessed']


class PortalNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortalNotification
        fields = ['id', 'user', 'title', 'body', 'is_read', 'timestamp']


class PreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortalPreference
        fields = ['id', 'profile', 'key', 'value']
