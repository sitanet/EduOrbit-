from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from django.db.models import Avg, Max, Min, StdDev
from backend.apps.emrp.models import ExamResult, PromotionRecommendation, Examination
from backend.apps.emrp.api.serializers import (
    ResultSerializer, PromotionSerializer
)
from backend.apps.core.events import event_bus, DomainEvent

class ExamResultAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        results = ExamResult.objects.filter(tenant=request.tenant)
        serializer = ResultSerializer(results, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = ResultSerializer(data=request.data)
        if serializer.is_valid():
            res = serializer.save(tenant=request.tenant)
            event_bus.publish(DomainEvent("result.calculated", tenant_id=str(request.tenant.id), data={"id": str(res.id)}))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BroadsheetAPIView(APIView):
    """
    Computes analytical averages for a specific Exam cohort.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, exam_id):
        exam = get_object_or_404(Examination, id=exam_id, tenant=request.tenant)
        results = ExamResult.objects.filter(exam=exam, tenant=request.tenant)
        
        # Calculate statistics
        stats = results.aggregate(
            average_score=Avg('computed_score'),
            highest_score=Max('computed_score'),
            lowest_score=Min('computed_score'),
            standard_dev=StdDev('computed_score')
        )
        
        return Response({
            "exam_title": exam.title,
            "total_candidates": results.count(),
            "average": str(stats.get('average_score') or 0),
            "highest": str(stats.get('highest_score') or 0),
            "lowest": str(stats.get('lowest_score') or 0),
            "std_dev": str(stats.get('standard_dev') or 0)
        }, status=status.HTTP_200_OK)


class PromotionsPreviewAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        promotions = PromotionRecommendation.objects.filter(tenant=request.tenant)
        serializer = PromotionSerializer(promotions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
