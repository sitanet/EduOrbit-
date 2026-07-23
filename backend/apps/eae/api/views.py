from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from django.utils import timezone
from backend.apps.eae.models import (
    Question, Assessment, AssessmentAttempt, AttemptAnswer, AssessmentResult
)
from backend.apps.eae.api.serializers import (
    QuestionSerializer, AssessmentSerializer, AttemptSerializer, ResultSerializer
)
from backend.apps.core.events import event_bus, DomainEvent

class QuestionAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        questions = Question.objects.filter(tenant=request.tenant)
        serializer = QuestionSerializer(questions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = QuestionSerializer(data=request.data)
        if serializer.is_valid():
            question = serializer.save(tenant=request.tenant)
            event_bus.publish(DomainEvent("question.created", tenant_id=str(request.tenant.id), data={"id": str(question.id)}))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AssessmentAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        assessments = Assessment.objects.filter(tenant=request.tenant)
        serializer = AssessmentSerializer(assessments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = AssessmentSerializer(data=request.data)
        if serializer.is_valid():
            assessment = serializer.save(tenant=request.tenant)
            event_bus.publish(DomainEvent("assessment.published", tenant_id=str(request.tenant.id), data={"id": str(assessment.id)}))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AttemptAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        attempts = AssessmentAttempt.objects.filter(tenant=request.tenant)
        serializer = AttemptSerializer(attempts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = AttemptSerializer(data=request.data)
        if serializer.is_valid():
            attempt = serializer.save(tenant=request.tenant)
            event_bus.publish(DomainEvent("attempt.started", tenant_id=str(request.tenant.id), data={"id": str(attempt.id)}))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AutoMarkAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, attempt_id):
        attempt = get_object_or_404(AssessmentAttempt, id=attempt_id, tenant=request.tenant)
        answers = AttemptAnswer.objects.filter(attempt=attempt)
        
        total_points = 0
        earned_points = 0
        
        for ans in answers:
            total_points += ans.question.default_marks
            # Simple check MCQ logic
            if ans.question.question_type == 'mcq' and ans.selected_choice:
                if ans.selected_choice.is_correct:
                    ans.is_correct = True
                    ans.marks_earned = ans.question.default_marks
                    ans.save()
                    earned_points += ans.question.default_marks
                else:
                    ans.is_correct = False
                    ans.marks_earned = 0.00
                    ans.save()
                    
        # Update attempt status
        attempt.status = 'completed'
        attempt.time_submitted = timezone.now()
        attempt.save()
        
        percentage = (earned_points / total_points * 100) if total_points > 0 else 0
        result = AssessmentResult.objects.create(
            student=attempt.student,
            assessment=attempt.assessment,
            tenant=request.tenant,
            total_score=earned_points,
            percentage=percentage,
            grade='A' if percentage >= 70 else 'C'
        )
        
        event_bus.publish(DomainEvent("result.released", tenant_id=str(request.tenant.id), data={"id": str(result.id)}))
        return Response({
            "detail": "Assessment auto-marked successfully.",
            "earned_score": str(earned_points),
            "percentage": str(percentage)
        }, status=status.HTTP_200_OK)
