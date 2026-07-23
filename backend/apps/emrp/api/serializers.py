from rest_framework import serializers
from backend.apps.emrp.models import (
    ExamSession, Examination, ExaminationPaper, ExaminationSchedule,
    CandidateRegistration, ExamResult, ResultCorrection, PromotionRecommendation
)

class ExamSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamSession
        fields = ['id', 'school', 'academic_year', 'name']


class ExaminationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Examination
        fields = ['id', 'school', 'exam_session', 'title', 'status']


class PaperSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExaminationPaper
        fields = ['id', 'exam', 'assessment', 'formula_weight']


class ScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExaminationSchedule
        fields = ['id', 'paper', 'start_time', 'duration_minutes', 'room']


class CandidateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CandidateRegistration
        fields = ['id', 'student', 'exam', 'registered_at', 'eligible']


class ResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamResult
        fields = ['id', 'student', 'exam', 'raw_score', 'computed_score', 'letter_grade', 'gp', 'status']


class CorrectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResultCorrection
        fields = ['id', 'result', 'requested_score', 'status', 'reason', 'requested_by_user_id']


class PromotionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromotionRecommendation
        fields = ['id', 'student', 'recommended_class', 'decision']
