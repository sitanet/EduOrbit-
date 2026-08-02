import os
import sys
import json
import django

sys.path.insert(0, r"c:\Users\user\Desktop\Development\SMS")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.config.settings.local")
django.setup()

from django.test import RequestFactory
from backend.apps.tenants.models import Tenant
from backend.apps.hr.models import OnboardingDraft
from backend.apps.hr.api.kyc_views import AutoSaveDraftAPIView

def test_autosave():
    tenant = Tenant.objects.first() or Tenant.objects.create(name="Test Tenant")
    factory = RequestFactory()

    print("--- Scenario 1: Valid payload with no draft_id ---")
    payload1 = {"current_step": 1, "draft_data": {"first_name": "Test"}}
    req1 = factory.post("/hr/api/v1/onboarding/draft/auto-save/", data=json.dumps(payload1), content_type="application/json")
    req1.tenant = tenant
    res1 = AutoSaveDraftAPIView.as_view()(req1)
    print("STATUS 1:", res1.status_code, res1.content.decode("utf-8"))

    print("\n--- Scenario 2: draft_id is empty string '' ---")
    payload2 = {"draft_id": "", "current_step": 1, "draft_data": {"first_name": "Test"}}
    req2 = factory.post("/hr/api/v1/onboarding/draft/auto-save/", data=json.dumps(payload2), content_type="application/json")
    req2.tenant = tenant
    res2 = AutoSaveDraftAPIView.as_view()(req2)
    print("STATUS 2:", res2.status_code, res2.content.decode("utf-8"))

    print("\n--- Scenario 3: draft_id is 'undefined' or invalid UUID ---")
    payload3 = {"draft_id": "undefined", "current_step": 1, "draft_data": {"first_name": "Test"}}
    req3 = factory.post("/hr/api/v1/onboarding/draft/auto-save/", data=json.dumps(payload3), content_type="application/json")
    req3.tenant = tenant
    res3 = AutoSaveDraftAPIView.as_view()(req3)
    print("STATUS 3:", res3.status_code, res3.content.decode("utf-8"))

    print("\n--- Scenario 4: request.tenant is None ---")
    payload4 = {"current_step": 1, "draft_data": {"first_name": "Test"}}
    req4 = factory.post("/hr/api/v1/onboarding/draft/auto-save/", data=json.dumps(payload4), content_type="application/json")
    req4.tenant = None
    res4 = AutoSaveDraftAPIView.as_view()(req4)
    print("STATUS 4:", res4.status_code, res4.content.decode("utf-8"))

if __name__ == "__main__":
    test_autosave()

