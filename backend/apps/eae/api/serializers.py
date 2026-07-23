from rest_framework import serializers
from backend.apps.eae.models import (
    Question, QuestionChoice, AssessmentBlueprint,
    Assessment, AssessmentSection, AssessmentAttempt, AttemptAnswer, AssessmentResult
)

class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionChoice
        fields = ['id', 'choice_text', 'is_correct']


class QuestionSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True, read_only=True)
    
    class Meta:
        model = Question
        fields = ['id', 'school', 'subject', 'topic', 'question_text', 'question_type', 'complexity', 'default_marks', 'choices']


class BlueprintSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssessmentBlueprint
        fields = ['id', 'school', 'subject', 'number_of_questions', 'topics', 'difficulty_distribution']


class AssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assessment
        fields = ['id', 'school', 'blueprint', 'title', 'duration_minutes', 'is_active']


class SectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssessmentSection
        fields = ['id', 'assessment', 'name', 'order', 'marks_weight']


class AttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssessmentAttempt
        fields = ['id', 'student', 'assessment', 'status', 'time_started', 'time_submitted', 'recovery_payload']


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttemptAnswer
        fields = ['id', 'attempt', 'question', 'selected_choice', 'text_answer', 'is_correct', 'marks_earned']


class ResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssessmentResult
        fields = ['id', 'student', 'assessment', 'total_score', 'percentage', 'grade']
