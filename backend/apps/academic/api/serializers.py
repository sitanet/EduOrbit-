from rest_framework import serializers
from backend.apps.academic.models import (
    AcademicSettings, AcademicYear, AcademicPeriod, EducationLevel,
    AcademicLevel, AcademicClass, Subject, SubjectOffering,
    GradingScale, AssessmentComponent, PromotionPolicy, SchoolCalendarEvent
)

class AcademicSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicSettings
        fields = ['id', 'working_days', 'periods_per_day', 'passing_mark', 'max_subjects_per_student', 'weekend_teaching']


class AcademicYearSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicYear
        fields = ['id', 'name', 'code', 'start_date', 'end_date', 'status']


class AcademicPeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicPeriod
        fields = ['id', 'name', 'order', 'start_date', 'end_date', 'status']


class EducationLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = EducationLevel
        fields = ['id', 'name', 'code', 'is_active']


class AcademicLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicLevel
        fields = ['id', 'education_level', 'name', 'code']


class AcademicClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicClass
        fields = ['id', 'academic_level', 'name', 'capacity', 'display_order', 'color_code']


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ['id', 'code', 'name', 'category', 'credit_units', 'is_active']


class GradingScaleSerializer(serializers.ModelSerializer):
    class Meta:
        model = GradingScale
        fields = ['id', 'education_level', 'name', 'min_score', 'max_score', 'grade_letter', 'gpa_value', 'remarks']


class AssessmentComponentSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssessmentComponent
        fields = ['id', 'education_level', 'name', 'max_score', 'weight_percentage', 'sequence']


class PromotionPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = PromotionPolicy
        fields = ['id', 'academic_level', 'minimum_overall_score', 'minimum_subject_passes', 'attendance_percentage_required', 'manual_override_allowed']


class CalendarEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolCalendarEvent
        fields = ['id', 'title', 'category', 'start_date', 'end_date', 'recurrence_rule']
