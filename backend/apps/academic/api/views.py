from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from backend.apps.academic.models import (
    AcademicSettings, AcademicYear, EducationLevel, AcademicClass,
    Subject, GradingScale, SchoolCalendarEvent, PromotionPolicy
)
from backend.apps.academic.api.serializers import (
    AcademicSettingsSerializer, AcademicYearSerializer, EducationLevelSerializer,
    AcademicClassSerializer, SubjectSerializer, GradingScaleSerializer,
    CalendarEventSerializer, PromotionPolicySerializer
)
from backend.apps.core.events import event_bus, DomainEvent

class AcademicSettingsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        school_id = request.query_params.get('school_id')
        settings = get_object_or_404(AcademicSettings, school_id=school_id, tenant=request.tenant)
        serializer = AcademicSettingsSerializer(settings)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        school_id = request.data.get('school_id')
        settings = get_object_or_404(AcademicSettings, school_id=school_id, tenant=request.tenant)
        serializer = AcademicSettingsSerializer(settings, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AcademicYearAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        school_id = request.query_params.get('school_id')
        years = AcademicYear.objects.filter(school_id=school_id, tenant=request.tenant)
        serializer = AcademicYearSerializer(years, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        school_id = request.data.get('school_id')
        serializer = AcademicYearSerializer(data=request.data)
        if serializer.is_valid():
            year = serializer.save(school_id=school_id, tenant=request.tenant)
            event_bus.publish(DomainEvent("academicyear.created", tenant_id=str(request.tenant.id), data={"year": year.name}))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EducationLevelAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        school_id = request.query_params.get('school_id')
        levels = EducationLevel.objects.filter(school_id=school_id, tenant=request.tenant)
        serializer = EducationLevelSerializer(levels, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SubjectAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        school_id = request.query_params.get('school_id')
        subjects = Subject.objects.filter(school_id=school_id, tenant=request.tenant)
        serializer = SubjectSerializer(subjects, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
