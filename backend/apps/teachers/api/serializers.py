from rest_framework import serializers
from backend.apps.teachers.models import (
    Curriculum, SchemeOfWork, WeeklyPlan, LessonPlan,
    LessonInstance, LessonDelivery, Assignment, StudentObservation
)

class CurriculumSerializer(serializers.ModelSerializer):
    class Meta:
        model = Curriculum
        fields = ['id', 'name', 'code', 'version']


class SchemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchemeOfWork
        fields = ['id', 'school', 'curriculum', 'academic_year', 'academic_period', 'subject', 'target_level']


class WeeklyPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeeklyPlan
        fields = ['id', 'scheme', 'week_number', 'topics_covered']


class LessonPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonPlan
        fields = ['id', 'weekly_plan', 'title', 'objectives_summary', 'activities_description', 'version_number']


class LessonInstanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonInstance
        fields = ['id', 'schedule', 'lesson_plan', 'date']


class DeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonDelivery
        fields = ['id', 'lesson_instance', 'status', 'actual_start', 'actual_end']


class AssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assignment
        fields = ['id', 'school', 'teacher', 'academic_class', 'subject', 'title', 'content', 'assignment_type']


class ObservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentObservation
        fields = ['id', 'student', 'teacher', 'category', 'content', 'visibility']
