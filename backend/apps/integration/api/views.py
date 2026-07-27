from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from backend.apps.tenants.models import Tenant
from backend.apps.integration.models import (
    IntegrationProvider, WebhookEndpoint, AutomationWorkflow, ScheduledJob, APIClient, WebhookEvent
)
from backend.apps.integration.services.automation import (
    WebhookService, WorkflowAutomationService, APIManagementService
)

class IntegrationProviderListAPIView(APIView):
    def get(self, request):
        providers = IntegrationProvider.objects.all()
        data = [
            {"id": str(p.id), "name": p.name, "category": p.category, "is_active": p.is_active}
            for p in providers
        ]
        return Response({"status": "success", "count": len(data), "data": data})


class WebhookListAPIView(APIView):
    def get(self, request):
        endpoints = WebhookEndpoint.objects.all()
        data = [
            {"id": str(e.id), "target_url": e.target_url, "events": e.events_subscribed, "is_active": e.is_active}
            for e in endpoints
        ]
        return Response({"status": "success", "count": len(data), "data": data})


class WebhookCreateAPIView(APIView):
    def post(self, request):
        tenant_id = request.data.get('tenant_id')
        target_url = request.data.get('target_url')
        events = request.data.get('events', 'student.enrolled')

        try:
            tenant = Tenant.objects.get(id=tenant_id) if tenant_id else Tenant.objects.first()
            res = WebhookService.register_endpoint(tenant=tenant, target_url=target_url, events_subscribed=events)
            return Response({"status": "success", "data": res}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class WorkflowListAPIView(APIView):
    def get(self, request):
        workflows = AutomationWorkflow.objects.all()
        data = [
            {"id": str(w.id), "name": w.name, "trigger_event": w.trigger_event, "action_type": w.action_type}
            for w in workflows
        ]
        return Response({"status": "success", "count": len(data), "data": data})


class WorkflowCreateAPIView(APIView):
    def post(self, request):
        name = request.data.get('name')
        trigger_event = request.data.get('trigger_event')
        action_type = request.data.get('action_type')

        try:
            tenant = Tenant.objects.first()
            res = WorkflowAutomationService.create_workflow(tenant=tenant, name=name, trigger_event=trigger_event, action_type=action_type)
            return Response({"status": "success", "data": res}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class JobListAPIView(APIView):
    def get(self, request):
        jobs = ScheduledJob.objects.all()
        data = [
            {"id": str(j.id), "name": j.name, "cron": j.cron_expression, "task_name": j.task_name}
            for j in jobs
        ]
        return Response({"status": "success", "count": len(data), "data": data})


class APIClientListAPIView(APIView):
    def get(self, request):
        clients = APIClient.objects.all()
        data = [
            {"id": str(c.id), "name": c.client_name, "client_key": c.client_key, "rate_limit": c.rate_limit_per_minute}
            for c in clients
        ]
        return Response({"status": "success", "count": len(data), "data": data})


class EventListAPIView(APIView):
    def get(self, request):
        events = WebhookEvent.objects.all()
        data = [
            {"id": str(e.id), "event_type": e.event_type, "status": e.status, "retry_count": e.retry_count}
            for e in events
        ]
        return Response({"status": "success", "count": len(data), "data": data})
