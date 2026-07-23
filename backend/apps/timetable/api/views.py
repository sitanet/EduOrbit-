from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from backend.apps.timetable.models import Resource, Schedule, ConflictReport
from backend.apps.timetable.api.serializers import (
    ResourceSerializer, ScheduleSerializer, ConflictReportSerializer
)
from backend.apps.core.events import event_bus, DomainEvent

class ResourceAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        school_id = request.query_params.get('school_id')
        resources = Resource.objects.filter(school_id=school_id, tenant=request.tenant)
        serializer = ResourceSerializer(resources, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        school_id = request.data.get('school_id')
        serializer = ResourceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(school_id=school_id, tenant=request.tenant)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ScheduleAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        school_id = request.query_params.get('school_id')
        schedules = Schedule.objects.filter(school_id=school_id, tenant=request.tenant)
        serializer = ScheduleSerializer(schedules, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        school_id = request.data.get('school_id')
        serializer = ScheduleSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        data = serializer.validated_data
        
        # Real-time Conflict validation logic
        teacher_id = data.get('lesson').teacher_id if data.get('lesson') else None
        time_slot = data.get('time_slot')
        resource = data.get('resource')
        
        if time_slot:
            # Overlap check on Teacher availability
            if teacher_id and Schedule.objects.filter(
                lesson__teacher_id=teacher_id,
                time_slot=time_slot,
                tenant=request.tenant
            ).exists():
                ConflictReport.objects.create(
                    school_id=school_id,
                    tenant=request.tenant,
                    conflict_type='teacher_clash',
                    description=f"Teacher #{teacher_id} is already scheduled at this slot.",
                    severity='error'
                )
                event_bus.publish(DomainEvent("conflict.detected", tenant_id=str(request.tenant.id), data={"type": "teacher_clash"}))
                return Response({"detail": "Teacher conflict detected. Overlap blocked."}, status=status.HTTP_409_CONFLICT)
                
            # Overlap check on Resource allocation
            if resource and Schedule.objects.filter(
                resource=resource,
                time_slot=time_slot,
                tenant=request.tenant
            ).exists():
                ConflictReport.objects.create(
                    school_id=school_id,
                    tenant=request.tenant,
                    conflict_type='room_clash',
                    description=f"Room #{resource.id} is already occupied at this slot.",
                    severity='error'
                )
                event_bus.publish(DomainEvent("conflict.detected", tenant_id=str(request.tenant.id), data={"type": "room_clash"}))
                return Response({"detail": "Resource conflict detected. Overlap blocked."}, status=status.HTTP_409_CONFLICT)
                
        schedule = serializer.save(school_id=school_id, tenant=request.tenant)
        event_bus.publish(DomainEvent("lesson.scheduled", tenant_id=str(request.tenant.id), data={"id": str(schedule.id)}))
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ScheduleDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, pk, tenant):
        return get_object_or_404(Schedule, id=pk, tenant=tenant)

    def put(self, request, pk):
        schedule = self.get_object(pk, request.tenant)
        serializer = ScheduleSerializer(schedule, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        schedule = self.get_object(pk, request.tenant)
        schedule.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ResourceDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, pk, tenant):
        return get_object_or_404(Resource, id=pk, tenant=tenant)

    def put(self, request, pk):
        resource = self.get_object(pk, request.tenant)
        serializer = ResourceSerializer(resource, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        resource = self.get_object(pk, request.tenant)
        resource.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ConflictReportAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        school_id = request.query_params.get('school_id')
        reports = ConflictReport.objects.filter(school_id=school_id, tenant=request.tenant)
        serializer = ConflictReportSerializer(reports, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

