from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from backend.apps.students.models import (
    AcademicPlacementHistory, ClassPromotion, StudentTimeline, student_state_machine
)
from backend.apps.students.api.serializers import (
    PlacementSerializer, PromotionSerializer, TimelineSerializer
)
from backend.apps.core.events import event_bus, DomainEvent

class PlacementAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        student_id = request.query_params.get('student_id')
        placements = AcademicPlacementHistory.objects.filter(student_id=student_id, tenant=request.tenant)
        serializer = PlacementSerializer(placements, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = PlacementSerializer(data=request.data)
        if serializer.is_valid():
            placement = serializer.save(tenant=request.tenant)
            event_bus.publish(DomainEvent("student.placed", tenant_id=str(request.tenant.id), data={"student": placement.student.student_number}))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PromotionAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = PromotionSerializer(data=request.data)
        if serializer.is_valid():
            promotion = serializer.save(tenant=request.tenant)
            
            # Record promotion event in student timeline
            StudentTimeline.objects.create(
                student=promotion.student,
                tenant=request.tenant,
                event_type="promoted",
                title=f"Promoted to {promotion.new_class.name}",
                description=promotion.reason or "Automatic session promotion"
            )
            
            event_bus.publish(DomainEvent("student.promoted", tenant_id=str(request.tenant.id), data={"student": promotion.student.student_number}))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TimelineAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, student_id):
        timeline = StudentTimeline.objects.filter(student_id=student_id, tenant=request.tenant)
        serializer = TimelineSerializer(timeline, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
