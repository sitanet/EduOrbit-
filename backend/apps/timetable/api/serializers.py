from rest_framework import serializers
from backend.apps.timetable.models import (
    BellSchedule, TimeSlot, Resource, ScheduleType,
    Lesson, Schedule, ConflictReport
)

class BellScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = BellSchedule
        fields = ['id', 'school', 'name', 'description']


class TimeSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeSlot
        fields = ['id', 'bell_schedule', 'day_of_week', 'start_time', 'end_time', 'is_break']


class ResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resource
        fields = ['id', 'school', 'name', 'capacity', 'resource_type', 'status', 'availability']


class ScheduleTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduleType
        fields = ['id', 'name', 'code']


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ['id', 'school', 'subject', 'teacher', 'academic_class', 'duration_minutes']


class ScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schedule
        fields = ['id', 'school', 'schedule_type', 'lesson', 'resource', 'time_slot', 'title', 'start_time', 'end_time', 'recurrence_rule']


class ConflictReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConflictReport
        fields = ['id', 'school', 'conflict_type', 'description', 'severity', 'resolved_at', 'resolved_by_user_id']
