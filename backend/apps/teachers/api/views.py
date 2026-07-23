from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from backend.apps.teachers.models import Curriculum, LessonPlan, Assignment, StudentObservation
from backend.apps.teachers.api.serializers import (
    CurriculumSerializer, LessonPlanSerializer, AssignmentSerializer, ObservationSerializer
)
from backend.apps.core.events import event_bus, DomainEvent

class CurriculumAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        curricula = Curriculum.objects.all()
        serializer = CurriculumSerializer(curricula, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class LessonPlanAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        plans = LessonPlan.objects.filter(tenant=request.tenant)
        serializer = LessonPlanSerializer(plans, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = LessonPlanSerializer(data=request.data)
        if serializer.is_valid():
            plan = serializer.save(tenant=request.tenant)
            event_bus.publish(DomainEvent("lesson.planned", tenant_id=str(request.tenant.id), data={"id": str(plan.id)}))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AssignmentAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        assignments = Assignment.objects.filter(tenant=request.tenant)
        serializer = AssignmentSerializer(assignments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = AssignmentSerializer(data=request.data)
        if serializer.is_valid():
            assignment = serializer.save(tenant=request.tenant)
            event_bus.publish(DomainEvent("homework.assigned", tenant_id=str(request.tenant.id), data={"id": str(assignment.id)}))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ObservationAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ObservationSerializer(data=request.data)
        if serializer.is_valid():
            observation = serializer.save(tenant=request.tenant)
            
            # Feed into Student Timeline
            from backend.apps.students.models import StudentTimeline
            StudentTimeline.objects.create(
                student=observation.student,
                tenant=request.tenant,
                event_type="observation",
                title=f"New Observation: {observation.category.capitalize()}",
                description=observation.content[:150]
            )
            
            event_bus.publish(DomainEvent("observation.recorded", tenant_id=str(request.tenant.id), data={"id": str(observation.id)}))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
