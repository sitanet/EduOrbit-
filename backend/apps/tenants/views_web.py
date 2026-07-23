from django.shortcuts import render, redirect
from django.views import View
from django.http import HttpResponse
from backend.apps.tenants.services import TenantOnboardingService
from backend.apps.tenants.models import Tenant, School, TenantSubscription

class OnboardWizardWebView(View):
    def get(self, request):
        return render(request, 'tenants/wizard.html')

    def post(self, request):
        # Step-by-step onboarding wizard execution validation
        org_name = request.POST.get('org_name')
        admin_email = request.POST.get('admin_email')
        admin_username = request.POST.get('admin_username')
        admin_password = request.POST.get('admin_password')
        billing_model = request.POST.get('billing_model', 'school_pays')
        school_name = request.POST.get('school_name')
        
        try:
            tenant, school, admin_user = TenantOnboardingService.onboard_organization(
                org_name=org_name,
                admin_email=admin_email,
                admin_username=admin_username,
                admin_password_plain=admin_password,
                billing_model=billing_model,
                school_name=school_name
            )
        except Exception as e:
            return HttpResponse(
                f'<div class="p-4 mb-4 text-sm text-red-800 rounded-xl bg-red-50 dark:bg-slate-900 dark:text-red-400 border border-red-200 dark:border-red-900/30" role="alert">'
                f'<span class="font-semibold">Failed provisioning organization:</span> {str(e)}'
                f'</div>'
            )

        subdomain = tenant.branding_config.get('subdomain', 'school')
        return HttpResponse(
            f'<div class="p-4 mb-4 text-sm text-emerald-800 rounded-xl bg-emerald-50 dark:bg-slate-905 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-900/30" role="alert">'
            f'<h3 class="font-bold text-base mb-1">Provisioning Successful!</h3>'
            f'<p class="mb-2">Your local school testing URL has been generated: '
            f'<a href="http://{subdomain}.localhost:8000/" target="_blank" class="text-white bg-slate-800/80 hover:underline px-2 py-1 rounded font-mono">http://{subdomain}.localhost:8000/</a></p>'
            f'<p>Redirecting to login workspace...</p>'
            f'</div>'
            f'<script>setTimeout(() => {{ window.location.href = "/login/"; }}, 4000);</script>'
        )


class TenantDashboardWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        if request.user.is_superuser:
            schools = School.objects.all().select_related('tenant')
            tenant = None
            subscription = None
        else:
            schools = School.objects.filter(tenant=getattr(request, 'tenant', None))
            tenant = getattr(request, 'tenant', None)
            subscription = TenantSubscription.objects.filter(tenant=tenant).first()
        
        context = {
            'tenant': tenant,
            'schools': schools,
            'subscription': subscription,
            'is_superuser': request.user.is_superuser,
            'active_school_id': request.session.get('active_school_id')
        }
        return render(request, 'tenants/dashboard.html', context)


class SwitchSchoolView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
        school_id = request.GET.get('school_id')
        if school_id:
            # Query school globally to find its mapped tenant
            school = School.objects.filter(id=school_id).select_related('tenant').first()
            if school:
                request.session['active_school_id'] = str(school.id)
                request.session['active_tenant_id'] = str(school.tenant.id)
                request.session.modified = True
        return redirect('portal_dashboard_web')
