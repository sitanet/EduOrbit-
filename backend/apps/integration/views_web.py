from django.shortcuts import render, redirect
from django.views import View
from backend.apps.integration.models import WebhookEndpoint, IntegrationProvider, AutomationWorkflow

class IntegrationDashboardWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        tenant = getattr(request, 'tenant', None)
        webhooks = WebhookEndpoint.objects.filter(tenant=tenant) if tenant else WebhookEndpoint.objects.none()
        providers = IntegrationProvider.objects.filter(is_active=True)
        workflows = AutomationWorkflow.objects.filter(tenant=tenant) if tenant else AutomationWorkflow.objects.none()
        
        ctx = {
            'webhooks': webhooks,
            'providers': providers,
            'workflows': workflows,
            'tenant': tenant,
        }
        return render(request, 'integration/dashboard.html', ctx)
