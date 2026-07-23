from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from backend.apps.portal.models import PortalProfile, PortalNotification, PortalShortcut
from backend.apps.portal.api.serializers import (
    ProfileSerializer, PortalNotificationSerializer, ShortcutSerializer
)
from backend.apps.core.events import event_bus, DomainEvent

class PortalProfileAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profiles = PortalProfile.objects.filter(tenant=request.tenant)
        serializer = ProfileSerializer(profiles, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = ProfileSerializer(data=request.data)
        if serializer.is_valid():
            prof = serializer.save(tenant=request.tenant)
            event_bus.publish(DomainEvent("portal.profile_updated", tenant_id=str(request.tenant.id), data={"id": str(prof.id)}))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PortalNotificationAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        notifs = PortalNotification.objects.filter(tenant=request.tenant, user=request.user)
        serializer = PortalNotificationSerializer(notifs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = PortalNotificationSerializer(data=request.data)
        if serializer.is_valid():
            notif = serializer.save(tenant=request.tenant)
            event_bus.publish(DomainEvent("portal.notification_sent", tenant_id=str(request.tenant.id), data={"id": str(notif.id)}))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PortalShortcutAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        shortcuts = PortalShortcut.objects.filter(tenant=request.tenant)
        serializer = ShortcutSerializer(shortcuts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = ShortcutSerializer(data=request.data)
        if serializer.is_valid():
            short = serializer.save(tenant=request.tenant)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
