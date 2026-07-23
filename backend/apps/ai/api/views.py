from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from backend.apps.ai.models import AIConversation, AIMessage, PromptTemplate
from backend.apps.ai.api.serializers import (
    ConversationSerializer, MessageSerializer, TemplateSerializer
)
from backend.apps.core.events import event_bus, DomainEvent

class AIConversationAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        conversations = AIConversation.objects.filter(tenant=request.tenant)
        serializer = ConversationSerializer(conversations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = ConversationSerializer(data=request.data)
        if serializer.is_valid():
            conv = serializer.save(tenant=request.tenant)
            event_bus.publish(DomainEvent("ai.conversation_started", tenant_id=str(request.tenant.id), data={"id": str(conv.id)}))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AIMessageAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        messages = AIMessage.objects.filter(tenant=request.tenant)
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = MessageSerializer(data=request.data)
        if serializer.is_valid():
            msg = serializer.save(tenant=request.tenant)
            event_bus.publish(DomainEvent("ai.prompt_submitted", tenant_id=str(request.tenant.id), data={"id": str(msg.id)}))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PromptTemplateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        templates = PromptTemplate.objects.filter(tenant=request.tenant)
        serializer = TemplateSerializer(templates, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = TemplateSerializer(data=request.data)
        if serializer.is_valid():
            temp = serializer.save(tenant=request.tenant)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
