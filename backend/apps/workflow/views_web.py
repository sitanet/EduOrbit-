from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from backend.apps.tenants.models import School
from backend.apps.workflow.models import WorkflowDefinition, WorkflowTask, Document

class WorkflowDashboardWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        schools = School.objects.filter(tenant=getattr(request, 'tenant', None))
        active_school = schools.first()
        
        definitions = WorkflowDefinition.objects.filter(tenant=getattr(request, 'tenant', None))
        pending_tasks = WorkflowTask.objects.filter(tenant=getattr(request, 'tenant', None), is_completed=False).select_related('instance__version__workflow', 'step')
        documents = Document.objects.filter(tenant=getattr(request, 'tenant', None))
        
        context = {
            'schools': schools,
            'active_school': active_school,
            'definitions': definitions,
            'pending_tasks': pending_tasks,
            'documents': documents
        }
        return render(request, 'workflow/dashboard.html', context)


class ApprovalInboxWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        tasks = WorkflowTask.objects.filter(tenant=getattr(request, 'tenant', None), is_completed=False).select_related('instance__version__workflow', 'step')
        return render(request, 'workflow/inbox.html', {'tasks': tasks})
