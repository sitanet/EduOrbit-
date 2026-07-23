from rest_framework import serializers
from backend.apps.students.models import (
    SchoolHouse, StudentClub, StudentStatusHistory,
    AcademicPlacementHistory, ClassPromotion, StudentTimeline
)

class HouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolHouse
        fields = ['id', 'name', 'color_code', 'house_master_id', 'house_captain_id']


class ClubSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentClub
        fields = ['id', 'name', 'supervisor_user_id']


class StatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentStatusHistory
        fields = ['id', 'student', 'status', 'effective_date', 'reason']


class PlacementSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicPlacementHistory
        fields = ['id', 'student', 'academic_year', 'academic_class', 'house', 'campus', 'effective_date']


class PromotionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassPromotion
        fields = ['id', 'student', 'previous_class', 'new_class', 'effective_date', 'promotion_type', 'reason']


class TimelineSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentTimeline
        fields = ['id', 'student', 'event_type', 'title', 'description', 'occurred_at']
