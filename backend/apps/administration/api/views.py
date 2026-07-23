from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from backend.apps.administration.models import PlatformSetting, ModuleLicense, APIKey
from backend.apps.administration.api.serializers import (
    PlatformSettingSerializer, ModuleLicenseSerializer, APIKeySerializer
)
from backend.apps.core.events import event_bus, DomainEvent

class PlatformSettingAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        settings = PlatformSetting.objects.all()
        serializer = PlatformSettingSerializer(settings, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = PlatformSettingSerializer(data=request.data)
        if serializer.is_valid():
            setg = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ModuleLicenseAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        licenses = ModuleLicense.objects.filter(tenant=request.tenant)
        serializer = ModuleLicenseSerializer(licenses, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = ModuleLicenseSerializer(data=request.data)
        if serializer.is_valid():
            lic = serializer.save(tenant=request.tenant)
            event_bus.publish(DomainEvent("license.allocated", tenant_id=str(request.tenant.id), data={"id": str(lic.id)}))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class APIKeyAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        keys = APIKey.objects.filter(tenant=request.tenant)
        serializer = APIKeySerializer(keys, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = APIKeySerializer(data=request.data)
        if serializer.is_valid():
            key = serializer.save(tenant=request.tenant)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
