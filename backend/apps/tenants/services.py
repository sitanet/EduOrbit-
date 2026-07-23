import logging
from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from backend.apps.tenants.models import Tenant, School, TenantSubscription, SubscriptionPlan
from backend.apps.identity.models import User, TenantMembership, Role
from backend.apps.core.events import event_bus, DomainEvent
from backend.apps.core.logging import EduOrbitLogger

logger = logging.getLogger("eduorbit.tenants.services")

class TenantOnboardingService:
    """
    Onboarding orchestrator provisioning Tenants, Schools, trial plans,
    and registering school administrators.
    """
    @staticmethod
    @transaction.atomic
    def onboard_organization(org_name: str, 
                             admin_email: str, 
                             admin_username: str, 
                             admin_password_plain: str,
                             billing_model: str = 'school_pays', 
                             school_name: str = None, 
                             school_types: list = None,
                             branding_config: dict = None) -> tuple[Tenant, School, User]:
        # 1. Create Tenant (Organization)
        slug = org_name.lower().replace(" ", "-").replace(".", "").replace(",", "").strip()
        config = branding_config or {}
        if 'subdomain' not in config:
            config['subdomain'] = slug
            
        tenant = Tenant.objects.create(
            name=org_name,
            billing_model=billing_model,
            branding_config=config
        )
        
        # 2. Create the Tenant's first School
        s_name = school_name or f"{org_name} First School"
        school = School.objects.create(
            tenant=tenant,
            name=s_name,
            school_types=school_types or ['primary']
        )
        
        # 3. Create administrator User profile (Global account)
        admin_user = User.objects.create_user(
            username=admin_username,
            email=admin_email,
            password=admin_password_plain
        )
        
        # Resolve or create the default administrator role for this tenant
        admin_role, _ = Role.objects.get_or_create(
            code=f"tenant_admin_{tenant.id.hex[:8]}",
            name="Tenant Admin",
            tenant=tenant
        )
        
        # 4. Map user to this school with Administrator role
        TenantMembership.objects.create(
            user=admin_user,
            tenant=tenant,
            role=admin_role,
            status='active',
            primary_membership=True
        )

        # 5. Provision free trial subscription (30 days default)
        trial_plan, _ = SubscriptionPlan.objects.get_or_create(
            name="Trial Plan",
            interval="monthly",
            price=0.00,
            is_active=True
        )
        
        TenantSubscription.objects.create(
            tenant=tenant,
            plan=trial_plan,
            status="trial",
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            modules_licensed={
                "core": {"enabled": True},
                "ai_assistant": {"enabled": False}
            }
        )

        # 6. Publish Event logs
        event_bus.publish(DomainEvent("tenant.registered", tenant_id=str(tenant.id), actor_id=str(admin_user.id)))
        event_bus.publish(DomainEvent("trial.started", tenant_id=str(tenant.id), actor_id=str(admin_user.id)))
        
        EduOrbitLogger.audit(f"Tenant group '{org_name}' successfully onboarded.", tenant_id=tenant.id, user_id=admin_user.id)
        
        return tenant, school, admin_user
