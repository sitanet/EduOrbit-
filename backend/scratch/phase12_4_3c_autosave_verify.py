"""
Phase 12.4.3C — Enterprise Verification Script
Auto-Save Endpoint: All 10 scenarios
"""
import os, sys, json, uuid
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings.local')
sys.path.insert(0, r'c:\Users\user\Desktop\Development\SMS')
import django; django.setup()

from django.test import RequestFactory
from backend.apps.tenants.models import Tenant
from backend.apps.hr.models import OnboardingDraft
from backend.apps.hr.api.kyc_views import AutoSaveDraftAPIView
from django.contrib.auth import get_user_model

User = get_user_model()

tenant = Tenant.objects.first()
factory = RequestFactory()
view = AutoSaveDraftAPIView.as_view()

PASS = "✓ PASS"
FAIL = "✗ FAIL"

results = []

def run(label, payload, tenant_obj, expected_status, note=""):
    req = factory.post(
        '/hr/api/v1/onboarding/draft/auto-save/',
        data=json.dumps(payload),
        content_type='application/json'
    )
    req.tenant = tenant_obj
    try:
        res = view(req)
        body = json.loads(res.content.decode())
        status = PASS if res.status_code == expected_status else FAIL
        results.append({
            'label': label,
            'status': status,
            'http': res.status_code,
            'expected': expected_status,
            'body': body,
            'note': note
        })
    except Exception as e:
        results.append({
            'label': label,
            'status': FAIL,
            'http': 'EXCEPTION',
            'expected': expected_status,
            'body': str(e),
            'note': note
        })

# 1. New draft (no draft_id)
run("Scenario 1: New draft (no draft_id)",
    {"current_step": 1, "draft_data": {"first_name": "Test"}},
    tenant, 200)

# 2. Existing draft
d = OnboardingDraft.objects.create(tenant=tenant, current_step=1, draft_data={})
run("Scenario 2: Existing valid draft_id",
    {"draft_id": str(d.draft_id), "current_step": 2, "draft_data": {"employment_type": "full_time"}},
    tenant, 200)
d.refresh_from_db()
assert d.current_step == 2, f"Expected step 2, got {d.current_step}"

# 3. draft_id = ""
run("Scenario 3: draft_id = empty string",
    {"draft_id": "", "current_step": 1, "draft_data": {}},
    tenant, 200)

# 4. draft_id = null (JS null)
run("Scenario 4: draft_id = null (JSON null)",
    {"draft_id": None, "current_step": 1, "draft_data": {}},
    tenant, 200)

# 5. draft_id = "undefined" (JS bug)
run("Scenario 5: draft_id = 'undefined' string",
    {"draft_id": "undefined", "current_step": 1, "draft_data": {}},
    tenant, 200)

# 6. Invalid UUID format
run("Scenario 6: draft_id = invalid UUID format",
    {"draft_id": "not-a-uuid-at-all-12345", "current_step": 1, "draft_data": {}},
    tenant, 200)

# 7. Deleted draft (valid UUID but doesn't exist)
fake_uuid = str(uuid.uuid4())
run("Scenario 7: draft_id = valid UUID but deleted/non-existent",
    {"draft_id": fake_uuid, "current_step": 1, "draft_data": {}},
    tenant, 200)

# 8. Tenant missing
run("Scenario 8: Tenant missing (None)",
    {"current_step": 1, "draft_data": {}},
    None, 400)

# 9. draft_data is large/complex (Step 3 full payload)
step3_data = {
    "bank_name": "First Bank",
    "account_number": "3012345678",
    "account_name": "Test User",
    "pension_fund_administrator": "Stanbic IBTC",
    "pension_rsa_pin": "PEN12345678901",
    "nhf_number": "NHF/123/456",
    "nhis_number": "NHIS/123/456",
    "nsitf_number": "NSITF/123/456",
    "tin_number": "12345678-0001",
}
run("Scenario 9: Full Step 3 complex payload",
    {"current_step": 3, "draft_data": step3_data},
    tenant, 200)

# 10. draft_id = "null" string (JS bug)
run("Scenario 10: draft_id = 'null' string",
    {"draft_id": "null", "current_step": 1, "draft_data": {}},
    tenant, 200)

# Print results
print("\n" + "="*70)
print("PHASE 12.4.3C — AUTO-SAVE ENDPOINT VERIFICATION")
print("="*70)
all_pass = True
for r in results:
    icon = r['status']
    print(f"\n{icon} {r['label']}")
    print(f"   HTTP {r['http']} (expected {r['expected']})")
    if r['status'] == FAIL:
        all_pass = False
        print(f"   BODY: {r['body']}")
    else:
        body = r['body']
        if 'draft_id' in body:
            print(f"   draft_id: {body['draft_id']}")
        if 'message' in body:
            print(f"   message: {body['message']}")

print("\n" + "="*70)
print(f"OVERALL: {'ALL 10 SCENARIOS PASSED' if all_pass else 'FAILURES DETECTED'}")
print("="*70)
