from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from backend.apps.tenants.models import Tenant, School
from backend.apps.people.models import Person
from backend.apps.communication.models import Conversation, Message, SupportTicket
from backend.apps.communication.services.messaging import MessagingService, CampaignService, HelpdeskService, ParentEngagementService

class CommunicationV210TestCase(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Communication Tenant")
        self.school = School.objects.create(tenant=self.tenant, name="Saint Theresa International Academy")
        self.person1 = Person.objects.create(
            tenant=self.tenant, person_number="PER-COM-001", first_name="Gabriel", last_name="Mantis", date_of_birth="1985-06-12", gender="male"
        )
        self.person2 = Person.objects.create(
            tenant=self.tenant, person_number="PER-COM-002", first_name="Helen", last_name="Troy", date_of_birth="1990-09-24", gender="female"
        )
        self.client = APIClient()

    def test_messaging_campaign_helpdesk_and_circular_services(self):
        # 1. Internal Chat Messaging
        conv_res = MessagingService.create_conversation(tenant=self.tenant, participants=[self.person1, self.person2])
        conv = Conversation.objects.get(id=conv_res["conversation_id"])
        
        msg_res = MessagingService.send_message(conversation=conv, sender=self.person1, text="Hello Helen, please review the CRM lead report.")
        self.assertEqual(msg_res["status"], "success")

        # 2. Marketing Broadcast Campaign
        camp_res = CampaignService.create_broadcast(
            school=self.school, name="2026 Admissions Campaign", audience="all", title="Enrolment Now Open", content="Apply today for 2026/2027 term."
        )
        self.assertEqual(camp_res["status"], "success")

        # 3. Helpdesk Support Ticket
        tkt_res = HelpdeskService.create_ticket(
            school=self.school, requester=self.person2, subject="Portal Login Password Reset", description="Cannot log into parent portal.", priority="high"
        )
        self.assertEqual(tkt_res["status"], "success")

        ticket = SupportTicket.objects.get(id=tkt_res["ticket_id"])
        res_tkt = HelpdeskService.resolve_ticket(ticket=ticket)
        self.assertEqual(res_tkt["ticket_status"], "resolved")

        # 4. Parent Engagement Circular
        circ_res = ParentEngagementService.send_circular(
            school=self.school, title="End of Term PTA Meeting", content="All parents are invited to the hall on Friday."
        )
        self.assertEqual(circ_res["status"], "success")

    def test_communication_api_endpoints(self):
        # 1. Support Tickets List API
        tkt_url = '/communication/api/v1/tickets/'
        resp = self.client.get(tkt_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # 2. Support Ticket Creation API
        create_tkt_url = '/communication/api/v1/tickets/create/'
        payload = {
            "school_id": str(self.school.id),
            "requester_id": str(self.person1.id),
            "subject": "Fee Receipt Verification",
            "description": "Please confirm payment receipt #1002.",
            "priority": "medium"
        }
        tkt_resp = self.client.post(create_tkt_url, payload, format='json')
        self.assertEqual(tkt_resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(tkt_resp.data["status"], "success")
