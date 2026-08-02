from django.test import TestCase
from backend.apps.tenants.models import Tenant
from backend.apps.configuration.models import TenantConfiguration

class BaseModelTests(TestCase):
    def setUp(self):
        # Create a test tenant
        self.tenant = Tenant.objects.create(
            name="Test School",
            branding_config={"subdomain": "testschool"}
        )
        
    def test_tenant_creation(self):
        self.assertEqual(self.tenant.name, "Test School")
        self.assertIsNotNone(self.tenant.id)

    def test_soft_delete_and_tenant_scoped_model(self):
        # Create tenant-scoped configuration object
        config = TenantConfiguration.objects.create(
            tenant=self.tenant,
            key="academic_year",
            value={"current": "2026-2027"}
        )
        
        # Verify it exists in active objects
        self.assertEqual(TenantConfiguration.objects.filter(key="academic_year").count(), 1)
        
        # Perform soft delete
        config.delete()
        
        # Verify it is excluded from default manager (objects)
        self.assertEqual(TenantConfiguration.objects.filter(key="academic_year").count(), 0)
        
        # Verify it is still accessible via all_objects manager
        self.assertEqual(TenantConfiguration.all_objects.filter(key="academic_year").count(), 1)
        
        # Restore configuration
        config.restore()
        self.assertEqual(TenantConfiguration.objects.filter(key="academic_year").count(), 1)
