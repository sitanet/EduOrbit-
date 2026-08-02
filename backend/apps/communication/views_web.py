from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from backend.apps.tenants.models import School
from backend.apps.communication.models import Announcement, Conversation, Message

class CEHDashboardWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        tenant = getattr(request, 'tenant', None)
        schools = School.objects.filter(tenant=tenant)
        active_school = schools.first()

        announcements = Announcement.objects.filter(
            tenant=tenant
        ).order_by('-publish_at')

        context = {
            'schools': schools,
            'active_school': active_school,
            'announcements': announcements,
            'high_priority_count': announcements.filter(priority='emergency').count(),
        }
        return render(request, 'communication/dashboard.html', context)

    def post(self, request):
        """Handle Quick Compose announcement form submission."""
        if not request.user.is_authenticated:
            return redirect('login_web')

        tenant = getattr(request, 'tenant', None)
        action = request.POST.get('action')

        if action == 'publish_announcement':
            title = request.POST.get('title', '').strip()
            content = request.POST.get('content', '').strip()
            priority = request.POST.get('priority', 'general')
            audience = request.POST.get('audience', 'all')

            schools = School.objects.filter(tenant=tenant)
            active_school = schools.first()

            if title and content and active_school:
                Announcement.objects.create(
                    tenant=tenant,
                    school=active_school,
                    title=title,
                    content=content,
                    priority=priority,
                    visibility=audience,
                )

        # PRG pattern — redirect back to avoid double-submit on refresh
        return redirect('ceh_dashboard_web')


from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.utils import timezone
from backend.apps.people.models import Person

class ChatWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        tenant = getattr(request, 'tenant', None)
        conversations = Conversation.objects.filter(tenant=tenant).prefetch_related('participants')
        
        active_conv_id = request.GET.get('conversation_id')
        active_conversation = None
        messages = []
        
        if active_conv_id:
            try:
                active_conversation = Conversation.objects.get(id=active_conv_id, tenant=tenant)
            except Conversation.DoesNotExist:
                active_conversation = None
        elif conversations.exists():
            active_conversation = conversations.first()
            
        if active_conversation:
            messages = active_conversation.messages.all().select_related('sender').order_by('created_at')
            
        for conv in conversations:
            participants = conv.participants.exclude(user=request.user)
            if participants.exists():
                conv.display_title = ", ".join([f"{p.first_name} {p.last_name}" for p in participants])
            else:
                conv.display_title = "Conversation Group"
                
        if active_conversation:
            other_participants = active_conversation.participants.exclude(user=request.user)
            if other_participants.exists():
                active_conversation.display_title = ", ".join([f"{p.first_name} {p.last_name}" for p in other_participants])
            else:
                active_conversation.display_title = "Conversation Group"
                
        context = {
            'conversations': conversations,
            'active_conversation': active_conversation,
            'messages': messages
        }
        return render(request, 'communication/chat.html', context)

    def post(self, request):
        if not request.user.is_authenticated:
            return HttpResponse("Unauthorized", status=401)
            
        tenant = getattr(request, 'tenant', None)
        conversation_id = request.POST.get('conversation_id')
        text = request.POST.get('text', '').strip()
        
        if not text:
            return HttpResponse("", status=400)
            
        try:
            conversation = Conversation.objects.get(id=conversation_id, tenant=tenant)
            person = request.user.person_profile
            
            message = Message.objects.create(
                tenant=tenant,
                conversation=conversation,
                sender=person,
                text=text,
                created_at=timezone.now()
            )
            
            if request.headers.get('HX-Request'):
                return HttpResponse(
                    f'<div class="flex gap-3 justify-end">'
                    f'  <div class="bg-indigo-650 text-slate-900 dark:text-white rounded-2xl rounded-tr-none p-3 max-w-[70%]">'
                    f'    {message.text}'
                    f'  </div>'
                    f'  <div class="w-8 h-8 rounded-lg bg-slate-200 dark:bg-slate-600 flex items-center justify-center text-slate-900 dark:text-white text-xs font-bold shrink-0">'
                    f'    {message.sender.first_name[:1]}{message.sender.last_name[:1]}'
                    f'  </div>'
                    f'</div>'
                )
        except Exception as e:
            return HttpResponse(f"Error: {str(e)}", status=400)
            
        return redirect(f'/communication/chat-room/?conversation_id={conversation_id}')


class DemoRequestWebView(View):
    def get(self, request):
        return render(request, 'communication/request_demo.html')

    def post(self, request):
        name = request.POST.get('name')
        school_name = request.POST.get('school_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        student_count = request.POST.get('student_count')
        message = request.POST.get('message', '')
        
        return HttpResponse(
            f'<div class="p-6 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-center space-y-3">'
            f'  <div class="text-3xl">🎉</div>'
            f'  <h4 class="text-lg font-bold text-white">Demo Request Received!</h4>'
            f'  <p class="text-xs text-slate-350 leading-relaxed">'
            f'    Thank you, <span class="font-semibold text-indigo-400">{name}</span>. '
            f'    We have registered a demo request for <span class="font-semibold text-white">{school_name}</span>. '
            f'    Our team will contact you at <span class="font-semibold text-white">{email}</span> shortly.'
            f'  </p>'
            f'</div>'
        )


class DocumentationWebView(View):
    def get(self, request):
        return render(request, 'docs/index.html')
