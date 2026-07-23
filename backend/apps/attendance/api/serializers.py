from rest_framework import serializers
from backend.apps.attendance.models import (
    AttendancePolicy, AttendanceSession, AttendanceRecord,
    AttendanceCorrection, OfflineSyncQueue
)

class PolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendancePolicy
        fields = ['id', 'school', 'min_attendance_percentage', 'late_grace_period_minutes', 'auto_mark_absent_minutes']


class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceSession
        fields = ['id', 'school', 'attendance_type', 'lesson_instance', 'date']


class RecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceRecord
        fields = ['id', 'session', 'person', 'status', 'source', 'reason', 'device', 'time_marked']


class CorrectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceCorrection
        fields = ['id', 'record', 'requested_status', 'status', 'reason', 'requested_by_user_id']


class SyncQueueSerializer(serializers.ModelSerializer):
    class Meta:
        model = OfflineSyncQueue
        fields = ['id', 'client_uuid', 'device', 'payload', 'sync_status', 'local_timestamp', 'server_timestamp']
