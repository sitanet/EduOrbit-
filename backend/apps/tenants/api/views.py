from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.utils import timezone
from backend.apps.tenants.api.serializers import TenantOnboardSerializer, CampusSerializer, DomainSerializer
from backend.apps.tenants.models import Campus, CustomDomain
from backend.apps.tenants.services import TenantOnboardingService
from backend.apps.core.events import event_bus, DomainEvent

class OnboardAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = TenantOnboardSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        data = serializer.validated_data
        tenant, school, admin_user = TenantOnboardingService.onboard_organization(
            org_name=data['org_name'],
            admin_email=data['admin_email'],
            admin_username=data['admin_username'],
            admin_password_plain=data['admin_password'],
            billing_model=data.get('billing_model', 'school_pays'),
            school_name=data.get('school_name'),
            school_types=data.get('school_types')
        )

        return Response({
            "tenant": {
                "id": str(tenant.id),
                "name": tenant.name
            },
            "school": {
                "id": str(school.id),
                "name": school.name
            },
            "admin": {
                "username": admin_user.username
            }
        }, status=status.HTTP_201_CREATED)


class CampusAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not request.tenant:
            return Response({"detail": "Active tenant context required."}, status=status.HTTP_400_BAD_REQUEST)
        campuses = Campus.objects.filter(tenant=request.tenant)
        serializer = CampusSerializer(campuses, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        if not request.tenant:
            return Response({"detail": "Active tenant context required."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = CampusSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        campus = serializer.save(tenant=request.tenant)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DomainVerificationAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            domain = CustomDomain.objects.get(id=pk, tenant=request.tenant)
        except CustomDomain.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        # Mock verification query checking DNS record resolves verification token
        domain.is_verified = True
        domain.ssl_active = True
        domain.save(update_fields=['is_verified', 'ssl_active'])
        
        event_bus.publish(DomainEvent("domain.verified", tenant_id=str(request.tenant.id), data={"domain": domain.domain_name}))

        return Response(DomainSerializer(domain).data, status=status.HTTP_200_OK)
