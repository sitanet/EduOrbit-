from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from backend.apps.lms.models import LearningModule, LearningUnit, StudentProgress
from backend.apps.lms.api.serializers import (
    ModuleSerializer, UnitSerializer, ProgressSerializer
)
from backend.apps.core.events import event_bus, DomainEvent

class ModuleAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        school_id = request.query_params.get('school_id')
        modules = LearningModule.objects.filter(school_id=school_id, tenant=request.tenant)
        serializer = ModuleSerializer(modules, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        school_id = request.data.get('school_id')
        serializer = ModuleSerializer(data=request.data)
        if serializer.is_valid():
            module = serializer.save(school_id=school_id, tenant=request.tenant)
            event_bus.publish(DomainEvent("module.created", tenant_id=str(request.tenant.id), data={"id": str(module.id)}))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UnitAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        module_id = request.query_params.get('module_id')
        units = LearningUnit.objects.filter(module_id=module_id, tenant=request.tenant)
        serializer = UnitSerializer(units, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        module_id = request.data.get('module_id')
        serializer = UnitSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(module_id=module_id, tenant=request.tenant)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProgressAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        student_id = request.query_params.get('student_id')
        progress = StudentProgress.objects.filter(student_id=student_id, tenant=request.tenant)
        serializer = ProgressSerializer(progress, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = ProgressSerializer(data=request.data)
        if serializer.is_valid():
            progress = serializer.save(tenant=request.tenant)
            
            # Fire completion events
            if progress.status == 'completed':
                event_bus.publish(DomainEvent("learning.completed", tenant_id=str(request.tenant.id), data={"id": str(progress.id)}))
                
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
