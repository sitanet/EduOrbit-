from django.db import transaction
from backend.apps.tenants.models import Tenant, School

class TenantOnboardingService:
    """
    Tenant & School Onboarding Provisioning Engine.
    """
    @classmethod
    @transaction.atomic
    def onboard_tenant(cls, organization_name, school_name):
        tenant = Tenant.objects.create(name=organization_name)
        school = School.objects.create(tenant=tenant, name=school_name)
        return {"status": "success", "tenant_id": str(tenant.id), "school_id": str(school.id)}
