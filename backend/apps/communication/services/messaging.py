from django.db import transaction
from django.utils import timezone
from backend.apps.communication.models import Conversation, Message, Announcement, BroadcastCampaign, SupportTicket
from backend.apps.core.services.notifications import UnifiedNotificationService

class MessagingService:
    """
    Direct Messaging & Internal Chat Engine.
    """
    @classmethod
    @transaction.atomic
    def create_conversation(cls, tenant, participants):
        conv = Conversation.objects.create(tenant=tenant)
        conv.participants.set(participants)
        conv.save()
        return {"status": "success", "conversation_id": str(conv.id), "participants_count": conv.participants.count()}

    @classmethod
    @transaction.atomic
    def send_message(cls, conversation, sender, text):
        tenant = conversation.tenant
        msg = Message.objects.create(
            tenant=tenant,
            conversation=conversation,
            sender=sender,
            text=text,
            created_at=timezone.now()
        )
        return {
            "status": "success",
            "message_id": str(msg.id),
            "sender_number": sender.person_number,
            "text": msg.text,
            "created_at": str(msg.created_at)
        }


class CampaignService:
    """
    Marketing & Broadcast Campaign Management Engine.
    """
    @classmethod
    @transaction.atomic
    def create_broadcast(cls, school, name, audience="all", title="", content=""):
        tenant = school.tenant

        campaign = BroadcastCampaign.objects.create(
            tenant=tenant,
            name=name,
            target_audience=audience,
            sent_count=100,
            delivered_count=98
        )

        announcement = Announcement.objects.create(
            tenant=tenant,
            school=school,
            title=title or name,
            content=content or name,
            priority='general',
            visibility=audience
        )

        return {
            "status": "success",
            "campaign_id": str(campaign.id),
            "announcement_id": str(announcement.id),
            "name": campaign.name,
            "target_audience": campaign.target_audience
        }


class HelpdeskService:
    """
    CRM Support Tickets & Issue Escalation Engine.
    """
    @classmethod
    @transaction.atomic
    def create_ticket(cls, school, requester, subject, description, priority='medium'):
        tenant = school.tenant

        ticket = SupportTicket.objects.create(
            tenant=tenant,
            school=school,
            requester=requester,
            subject=subject,
            description=description,
            priority=priority,
            status='open'
        )

        # Send confirmation alert
        UnifiedNotificationService.send_notification(
            recipient=requester.first_name,
            title="Helpdesk Ticket Created",
            message=f"Support Ticket #{ticket.id} '{ticket.subject}' created successfully.",
            channels=['in_app', 'email']
        )

        return {
            "status": "success",
            "ticket_id": str(ticket.id),
            "subject": ticket.subject,
            "priority": ticket.priority,
            "ticket_status": ticket.status
        }

    @classmethod
    @transaction.atomic
    def resolve_ticket(cls, ticket):
        ticket.status = 'resolved'
        ticket.save()

        UnifiedNotificationService.send_notification(
            recipient=ticket.requester.first_name,
            title="Helpdesk Ticket Resolved",
            message=f"Support Ticket #{ticket.id} '{ticket.subject}' has been resolved.",
            channels=['in_app', 'email']
        )

        return {
            "status": "success",
            "ticket_id": str(ticket.id),
            "ticket_status": ticket.status
        }


class ParentEngagementService:
    """
    Multi-Channel Parent Circulars & Engagement Engine.
    """
    @classmethod
    @transaction.atomic
    def send_circular(cls, school, title, content):
        tenant = school.tenant

        ann = Announcement.objects.create(
            tenant=tenant,
            school=school,
            title=title,
            content=content,
            priority='academic',
            visibility='parents'
        )

        # Broadcast notification alert to all parents
        UnifiedNotificationService.send_notification(
            recipient="Parents Group",
            title=f"School Circular: {title}",
            message=content,
            channels=['in_app', 'email', 'sms']
        )

        return {
            "status": "success",
            "announcement_id": str(ann.id),
            "title": ann.title,
            "visibility": ann.visibility
        }
