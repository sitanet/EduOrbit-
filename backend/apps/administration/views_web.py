from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from backend.apps.tenants.models import School
from backend.apps.administration.models import SubscriptionPlan, SchoolSubscription, PlatformAudit


class PlatformDashboardWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
        # Only staff/superusers can access the platform dashboard
        if not request.user.is_staff:
            return redirect('portal_dashboard_web')

        schools = School.objects.all()
        plans = SubscriptionPlan.objects.all()
        audits = PlatformAudit.objects.all().order_by('-timestamp')[:5]

        context = {
            'schools': schools,
            'plans': plans,
            'audits': audits,
            'active_school_id': request.session.get('active_school_id')
        }
        return render(request, 'administration/dashboard.html', context)


class SchoolSettingsWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
        tenant = getattr(request, 'tenant', None)
        
        if request.user.is_superuser:
            schools = School.objects.all().select_related('tenant')
        else:
            schools = School.objects.filter(tenant=tenant) if tenant else []
            
        subscriptions = []
        for school in schools:
            sub = SchoolSubscription.objects.filter(school=school).select_related('plan').first()
            subscriptions.append({
                'school': school,
                'plan': sub.plan if sub else None,
                'expiry_date': sub.expiry_date if sub else None,
            })
            
        return render(request, 'administration/settings.html', {'subscriptions': subscriptions})
