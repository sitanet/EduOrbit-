from django.test import TestCase
from backend.apps.tenants.models import Tenant
from backend.apps.people.models import Person
from backend.apps.hr.models.onboarding_draft import OnboardingDraft
from backend.apps.hr.services.kyc import SandboxKYCProvider, DojahKYCProvider
from backend.apps.hr.services.duplicate_detector import DuplicateDetectionService

class Phase2OnboardingTestCase(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Academy Phase 2")
        self.person = Person.objects.create(
            tenant=self.tenant,
            person_number="PER-201",
            first_name="Natasha",
            last_name="Romanoff",
            date_of_birth="1992-06-15",
            gender="female"
        )

    def test_sandbox_nin_verification(self):
        provider = SandboxKYCProvider()
        res = provider.verify_nin("12345678901")
        self.assertEqual(res["status"], "success")
        self.assertTrue(res["is_verified"])
        self.assertEqual(res["data"]["full_name"], "Natasha Romanoff")

    def test_sandbox_bvn_verification(self):
        provider = SandboxKYCProvider()
        res = provider.verify_bvn("22345678901")
        self.assertEqual(res["status"], "success")
        self.assertTrue(res["is_verified"])

    def test_bank_account_resolution(self):
        provider = SandboxKYCProvider()
        res = provider.resolve_bank_account("058", "0123456789")
        self.assertEqual(res["status"], "success")
        self.assertTrue(res["is_resolved"])
        self.assertEqual(res["data"]["account_name"], "NATASHA ROMANOFF")

    def test_duplicate_detection(self):
        res = DuplicateDetectionService.check_duplicates(self.tenant, email="nonexistent@eduorbit.com")
        self.assertFalse(res["has_duplicates"])

    def test_onboarding_draft_auto_save(self):
        draft = OnboardingDraft.objects.create(
            tenant=self.tenant,
            current_step=2,
            draft_data={"first_name": "Natasha", "nin": "12345678901"}
        )
        self.assertEqual(draft.current_step, 2)
        self.assertEqual(draft.draft_data["nin"], "12345678901")
