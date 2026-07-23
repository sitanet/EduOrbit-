from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from backend.apps.tenants.models import School
from backend.apps.ai.models import AIConversation, PromptTemplate, KnowledgeDocument

class AIWorkspaceWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        schools = School.objects.filter(tenant=getattr(request, 'tenant', None))
        active_school = schools.first()
        
        conversations = AIConversation.objects.filter(tenant=getattr(request, 'tenant', None), user=request.user)
        documents = KnowledgeDocument.objects.filter(tenant=getattr(request, 'tenant', None))
        
        context = {
            'schools': schools,
            'active_school': active_school,
            'conversations': conversations,
            'documents': documents
        }
        return render(request, 'ai/dashboard.html', context)


class PromptLibraryWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        prompts = PromptTemplate.objects.filter(tenant=getattr(request, 'tenant', None))
        return render(request, 'ai/prompts.html', {'prompts': prompts})
