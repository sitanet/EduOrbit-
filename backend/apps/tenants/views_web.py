from django.shortcuts import render, redirect
from django.views import View
from django.http import HttpResponse
from backend.apps.tenants.models import TenantSubscription, School
from backend.apps.tenants.services import TenantDashboardService

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
            # Direct inline onboarding implementation as workaround
            tenant, school, admin_user = self._onboard_organization(
                org_name=org_name,
                admin_email=admin_email,
                admin_username=admin_username,
                admin_password_plain=admin_password,
                billing_model=billing_model,
                school_name=school_name
            )
        except Exception as e:
            return HttpResponse(f"Failed provisioning organization: {e}", status=500)
        
        return HttpResponse(f"Organization '{org_name}' successfully onboarded!", status=201)
    
    def _onboard_organization(self, org_name, admin_email, admin_username, admin_password_plain, 
                             billing_model='school_pays', school_name=None):
        """Simplified onboarding implementation"""
        from django.db import transaction
        from django.utils import timezone
        from datetime import timedelta
        from backend.apps.tenants.models import Tenant, School, TenantSubscription
        from backend.apps.administration.models import SubscriptionPlan
        from backend.apps.identity.models import User, TenantMembership, Role
        
        with transaction.atomic():
            # 1. Create Tenant
            slug = org_name.lower().replace(" ", "-").replace(".", "").replace(",", "").strip()
            config = {'subdomain': slug}
            
            tenant = Tenant.objects.create(
                name=org_name,
                billing_model=billing_model,
                branding_config=config
            )
            
            # 2. Create School
            s_name = school_name or f"{org_name} First School"
            school = School.objects.create(
                tenant=tenant,
                name=s_name,
                school_types=['primary']
            )
            
            # 3. Create admin user
            admin_user = User.objects.create_user(
                username=admin_username,
                email=admin_email,
                password=admin_password_plain
            )
            
            # 4. Create admin role
            admin_role, _ = Role.objects.get_or_create(
                code=f"tenant_admin_{tenant.id.hex[:8]}",
                name="Tenant Admin",
                tenant=tenant
            )
            
            # 5. Create membership
            TenantMembership.objects.create(
                user=admin_user,
                tenant=tenant,
                role=admin_role,
                status='active',
                primary_membership=True
            )
            
            # 6. Create trial subscription
            from backend.apps.tenants.models import SubscriptionPlan as TenantSubPlan
            trial_plan, _ = TenantSubPlan.objects.get_or_create(
                name="Trial Plan",
                defaults={
                    "monthly_price": 0.00,
                    "is_active": True
                }
            )
            
            TenantSubscription.objects.create(
                tenant=tenant,
                plan=trial_plan,
                status="TRIAL",
                start_date=timezone.now(),
                end_date=timezone.now() + timedelta(days=30),
                modules_licensed={
                    "core": {"enabled": True},
                    "ai_assistant": {"enabled": False}
                }
            )
            
            return tenant, school, admin_user


class TenantDashboardWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        tenant = getattr(request, 'tenant', None)
        
        # Use service layer for all data queries
        dashboard_data = TenantDashboardService.get_dashboard_data(request.user, tenant)
        
        # Add session data to context
        context = {
            **dashboard_data,
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
