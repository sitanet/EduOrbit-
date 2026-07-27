from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from backend.apps.tenants.models import Tenant, School
from backend.apps.integration.models import WebhookEndpoint, AutomationWorkflow
from backend.apps.integration.services.automation import (
    IntegrationProviderService, EventBusService, WebhookService, WorkflowAutomationService,
    SchedulerService, SynchronizationService, APIManagementService
)

class IntegrationV260TestCase(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Integration Tenant")
        self.school = School.objects.create(tenant=self.tenant, name="MIT Enterprise Academy")
        self.client = APIClient()

    def test_integration_and_automation_services(self):
        # 1. Integration Provider Registration
        p_res = IntegrationProviderService.register_provider(name="Google Workspace", category="auth")
        self.assertEqual(p_res["status"], "success")

        # 2. Event Bus Service
        bus_res = EventBusService.publish_event(event_type="student.enrolled", payload={"student_id": "101"})
        self.assertEqual(bus_res["status"], "success")

        # 3. Webhook Registration & Delivery Service
        wh_res = WebhookService.register_endpoint(tenant=self.tenant, target_url="https://api.partner.org/webhook")
        self.assertEqual(wh_res["status"], "success")

        endpoint = WebhookEndpoint.objects.get(id=wh_res["endpoint_id"])
        proc_res = WebhookService.process_webhook(endpoint=endpoint, event_type="student.enrolled", payload={"student_id": "101"})
        self.assertEqual(proc_res["status"], "success")

        # 4. Workflow Automation Pipeline Service
        wf_res = WorkflowAutomationService.create_workflow(tenant=self.tenant, name="Onboarding Pipeline", trigger_event="student.enrolled", action_type="create_lms_account")
        self.assertEqual(wf_res["status"], "success")

        workflow = AutomationWorkflow.objects.get(id=wf_res["workflow_id"])
        trg_res = WorkflowAutomationService.trigger_workflow(workflow=workflow, context={"student_id": "101"})
        self.assertEqual(trg_res["status"], "success")

        # 5. Background Scheduler & External Synchronization
        job_res = SchedulerService.schedule_cron_job(tenant=self.tenant, name="Nightly Sync Job")
        self.assertEqual(job_res["status"], "success")

        sync_res = SynchronizationService.sync_external_system(tenant=self.tenant, external_system="Microsoft 365")
        self.assertEqual(sync_res["status"], "success")

        # 6. API Key Management
        api_res = APIManagementService.create_api_client(tenant=self.tenant, client_name="Partner Portal App")
        self.assertEqual(api_res["status"], "success")

    def test_integration_api_endpoints(self):
        # 1. Integration Providers API
        p_url = '/integration/api/v1/providers/'
        p_resp = self.client.get(p_url)
        self.assertEqual(p_resp.status_code, status.HTTP_200_OK)

        # 2. Webhooks List API
        wh_url = '/integration/api/v1/webhooks/'
        wh_resp = self.client.get(wh_url)
        self.assertEqual(wh_resp.status_code, status.HTTP_200_OK)

        # 3. Webhook Creation API
        create_wh_url = '/integration/api/v1/webhooks/create/'
        payload = {
            "target_url": "https://hooks.slack.com/services/test",
            "events": "invoice.paid"
        }
        create_resp = self.client.post(create_wh_url, payload, format='json')
        self.assertEqual(create_resp.status_code, status.HTTP_201_CREATED)

        # 4. Workflows List API
        wf_url = '/integration/api/v1/workflows/'
        wf_resp = self.client.get(wf_url)
        self.assertEqual(wf_resp.status_code, status.HTTP_200_OK)
