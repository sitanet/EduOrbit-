from rest_framework import serializers
from backend.apps.lms.models import (
    ContentType, LearningModule, LearningUnit, LearningContent,
    ContentLicense, LearningActivity, StudentProgress
)

class ContentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentType
        fields = ['id', 'name', 'code']


class ModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningModule
        fields = ['id', 'school', 'subject', 'topic', 'title', 'version']


class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningUnit
        fields = ['id', 'module', 'name', 'order']


class ContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningContent
        fields = ['id', 'unit', 'content_type', 'title']


class LicenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentLicense
        fields = ['id', 'content', 'downloadable', 'stream_only', 'expiry_date']


class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningActivity
        fields = ['id', 'unit', 'name', 'activity_type', 'learning_objective', 'content', 'assignment', 'order']


class ProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProgress
        fields = ['id', 'student', 'activity', 'status', 'first_access', 'last_access', 'completion_percentage', 'total_time_seconds']
