from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from backend.apps.admissions.models import (
    AdmissionCampaign, AdmissionIntake, AdmissionApplication, ApplicationDocument, AdmissionOffer
)
from backend.apps.admissions.api.serializers import (
    CampaignSerializer, IntakeSerializer, ApplicationSerializer,
    ApplicationDocumentSerializer, OfferSerializer
)
from backend.apps.admissions.services import EnrollmentService
from backend.apps.core.events import event_bus, DomainEvent

class CampaignAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        school_id = request.query_params.get('school_id')
        campaigns = AdmissionCampaign.objects.filter(school_id=school_id, tenant=request.tenant)
        serializer = CampaignSerializer(campaigns, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class IntakeAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        campaign_id = request.query_params.get('campaign_id')
        intakes = AdmissionIntake.objects.filter(campaign_id=campaign_id, tenant=request.tenant)
        serializer = IntakeSerializer(intakes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ApplicationAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        applications = AdmissionApplication.objects.filter(tenant=request.tenant)
        serializer = ApplicationSerializer(applications, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class EnrollmentAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        application_id = request.data.get('application_id')
        class_id = request.data.get('class_id')
        
        try:
            student_profile = EnrollmentService.enroll_applicant(
                application_id=application_id,
                class_id=class_id
            )
            return Response({
                "detail": "Applicant successfully promoted to Student Profile.",
                "student_number": student_profile.student_number
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
