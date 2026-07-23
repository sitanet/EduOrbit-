from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from backend.apps.communication.models import Announcement, Notification, Message
from backend.apps.communication.api.serializers import (
    AnnouncementSerializer, NotificationSerializer, MessageSerializer
)
from backend.apps.core.events import event_bus, DomainEvent

class AnnouncementAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        announcements = Announcement.objects.filter(tenant=request.tenant)
        serializer = AnnouncementSerializer(announcements, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = AnnouncementSerializer(data=request.data)
        if serializer.is_valid():
            ann = serializer.save(tenant=request.tenant)
            # Publish event
            event_bus.publish(DomainEvent("announcement.created", tenant_id=str(request.tenant.id), data={"id": str(ann.id)}))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NotificationAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        notifications = Notification.objects.filter(tenant=request.tenant)
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = NotificationSerializer(data=request.data)
        if serializer.is_valid():
            notif = serializer.save(tenant=request.tenant)
            event_bus.publish(DomainEvent("notification.sent", tenant_id=str(request.tenant.id), data={"id": str(notif.id)}))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MessageAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        messages = Message.objects.filter(tenant=request.tenant)
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = MessageSerializer(data=request.data)
        if serializer.is_valid():
            msg = serializer.save(tenant=request.tenant)
            event_bus.publish(DomainEvent("message.sent", tenant_id=str(request.tenant.id), data={"id": str(msg.id)}))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
