from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from backend.apps.tenants.models import School
from backend.apps.people.models import Person
from backend.apps.communication.models import Message, Conversation, SupportTicket
from backend.apps.communication.services.messaging import MessagingService, HelpdeskService

class MessageListAPIView(APIView):
    def get(self, request):
        messages = Message.objects.all()
        data = [
            {
                "id": str(m.id),
                "sender_number": m.sender.person_number,
                "text": m.text,
                "created_at": str(m.created_at)
            }
            for m in messages
        ]
        return Response({"status": "success", "count": len(data), "data": data})


class MessageSendAPIView(APIView):
    def post(self, request):
        conversation_id = request.data.get('conversation_id')
        sender_id = request.data.get('sender_id')
        text = request.data.get('text')

        try:
            conv = Conversation.objects.get(id=conversation_id)
            sender = Person.objects.get(id=sender_id)
            res = MessagingService.send_message(conversation=conv, sender=sender, text=text)
            return Response({"status": "success", "data": res}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class TicketCreateAPIView(APIView):
    def post(self, request):
        school_id = request.data.get('school_id')
        requester_id = request.data.get('requester_id')
        subject = request.data.get('subject')
        description = request.data.get('description')
        priority = request.data.get('priority', 'medium')

        try:
            school = School.objects.get(id=school_id)
            requester = Person.objects.get(id=requester_id)
            res = HelpdeskService.create_ticket(school=school, requester=requester, subject=subject, description=description, priority=priority)
            return Response({"status": "success", "data": res}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class TicketListAPIView(APIView):
    def get(self, request):
        tickets = SupportTicket.objects.all()
        data = [
            {
                "id": str(t.id),
                "requester": t.requester.person_number,
                "subject": t.subject,
                "priority": t.priority,
                "status": t.status
            }
            for t in tickets
        ]
        return Response({"status": "success", "count": len(data), "data": data})
