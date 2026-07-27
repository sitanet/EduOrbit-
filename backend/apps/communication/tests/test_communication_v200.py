from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from backend.apps.tenants.models import Tenant, School
from backend.apps.people.models import Person
from backend.apps.communication.models import Conversation, Message, SupportTicket
from backend.apps.communication.services.messaging import MessagingService, CampaignService, HelpdeskService, ParentEngagementService

class CommunicationV200TestCase(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Communication v200 Tenant")
        self.school = School.objects.create(tenant=self.tenant, name="Royal Academy of Science")
        self.person1 = Person.objects.create(
            tenant=self.tenant, person_number="PER-COM-201", first_name="Arthur", last_name="Pendelton", date_of_birth="1982-03-15", gender="male"
        )
        self.person2 = Person.objects.create(
            tenant=self.tenant, person_number="PER-COM-202", first_name="Gwen", last_name="Stacy", date_of_birth="1995-11-04", gender="female"
        )
        self.client = APIClient()

    def test_communication_v200_services(self):
        # 1. Conversation & Messaging
        conv_res = MessagingService.create_conversation(tenant=self.tenant, participants=[self.person1, self.person2])
        conv = Conversation.objects.get(id=conv_res["conversation_id"])
        
        msg_res = MessagingService.send_message(conversation=conv, sender=self.person1, text="Please send the CRM analytics report.")
        self.assertEqual(msg_res["status"], "success")

        # 2. Campaign Service
        camp_res = CampaignService.create_broadcast(
            school=self.school, name="Q3 Engagement Campaign", audience="all", title="Annual Sports Gala", content="Join us at the sports complex."
        )
        self.assertEqual(camp_res["status"], "success")

        # 3. Helpdesk Ticket Service
        tkt_res = HelpdeskService.create_ticket(
            school=self.school, requester=self.person2, subject="Invoice PDF Download Error", description="Unable to generate pdf receipt", priority="medium"
        )
        self.assertEqual(tkt_res["status"], "success")

    def test_communication_v200_api_endpoints(self):
        # 1. Tickets List API
        t_url = '/communication/api/v1/tickets/'
        t_resp = self.client.get(t_url)
        self.assertEqual(t_resp.status_code, status.HTTP_200_OK)

        # 2. Messages List API
        m_url = '/communication/api/v1/messages/'
        m_resp = self.client.get(m_url)
        self.assertEqual(m_resp.status_code, status.HTTP_200_OK)
