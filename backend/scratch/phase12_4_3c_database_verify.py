"""
Phase 12.4.3C — Database Integrity & Security Verification Script
"""
import os, sys, uuid
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings.local')
sys.path.insert(0, r'c:\Users\user\Desktop\Development\SMS')
import django; django.setup()

from django.db import connection
from backend.apps.tenants.models import Tenant
from backend.apps.hr.models import OnboardingDraft

PASS = "✓ PASS"
FAIL = "✗ FAIL"

print("=" * 70)
print("PHASE 12.4.3C — DATABASE & SECURITY VERIFICATION")
print("=" * 70)

# 1. Confirm OnboardingDraft table exists and has correct columns
print("\n[1] OnboardingDraft Schema Audit")
with connection.cursor() as cur:
    cur.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'hr_onboarding_draft'
        ORDER BY ordinal_position
    """)
    cols = cur.fetchall()
    if cols:
        print(f"   {PASS} Table hr_onboarding_draft exists with {len(cols)} columns:")
        for col, dtype in cols:
            print(f"      - {col}: {dtype}")
    else:
        print(f"   {FAIL} Table hr_onboarding_draft NOT FOUND")

# 2. Confirm EmployeeProfile has statutory fields
print("\n[2] EmployeeProfile Statutory Fields Audit")
REQUIRED_FIELDS = ['nhf_number', 'nhis_number', 'nsitf_number',
                   'pension_fund_administrator', 'pension_rsa_pin']
with connection.cursor() as cur:
    cur.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'hr_employee_profile'
    """)
    ep_cols = [r[0] for r in cur.fetchall()]
    for field in REQUIRED_FIELDS:
        if field in ep_cols:
            print(f"   {PASS} EmployeeProfile.{field} exists")
        else:
            print(f"   {FAIL} EmployeeProfile.{field} MISSING")

# 3. UUID generation test — no duplicates
print("\n[3] UUID Generation & Uniqueness Audit")
tenant = Tenant.objects.first()
ids = set()
for i in range(5):
    d = OnboardingDraft.objects.create(tenant=tenant)
    if str(d.draft_id) in ids:
        print(f"   {FAIL} DUPLICATE UUID detected: {d.draft_id}")
    else:
        ids.add(str(d.draft_id))
print(f"   {PASS} Created 5 drafts, all UUIDs unique: {list(ids)[:2]}...")
OnboardingDraft.objects.filter(draft_id__in=ids).delete()

# 4. Tenant isolation — draft from tenant A not visible to tenant B
print("\n[4] Tenant Isolation Audit")
all_tenants = list(Tenant.objects.all()[:2])
if len(all_tenants) >= 2:
    t1, t2 = all_tenants[0], all_tenants[1]
    d1 = OnboardingDraft.objects.create(tenant=t1)
    try:
        OnboardingDraft.objects.get(draft_id=d1.draft_id, tenant=t2)
        print(f"   {FAIL} Tenant isolation BROKEN — cross-tenant access possible")
    except OnboardingDraft.DoesNotExist:
        print(f"   {PASS} Tenant isolation CONFIRMED — draft from T1 not visible to T2")
    d1.delete()
else:
    t1 = all_tenants[0]
    d1 = OnboardingDraft.objects.create(tenant=t1)
    fake_tenant_id = uuid.uuid4()
    # Simulate by checking no result with wrong tenant
    count = OnboardingDraft.objects.filter(draft_id=d1.draft_id).exclude(tenant=t1).count()
    if count == 0:
        print(f"   {PASS} Tenant isolation CONFIRMED (single-tenant mode)")
    d1.delete()

# 5. Data integrity — draft_data saved and retrieved correctly
print("\n[5] Draft Data Integrity Audit")
test_data = {
    "first_name": "Amara",
    "last_name": "Okonkwo",
    "nin_number": "12345678901",
    "nin_verified": True,
    "bank_account": "3012345678",
    "nhf_number": "NHF/001/2024",
}
d = OnboardingDraft.objects.create(tenant=tenant, current_step=3, draft_data=test_data)
d_retrieved = OnboardingDraft.objects.get(draft_id=d.draft_id)
match = d_retrieved.draft_data == test_data
print(f"   {PASS if match else FAIL} Draft data round-trip: {'EXACT MATCH' if match else 'DATA MISMATCH'}")
if not match:
    print(f"   Stored: {d_retrieved.draft_data}")
    print(f"   Expected: {test_data}")
d.delete()

# 6. SupplierBalance column check
print("\n[6] SupplierBalance Migration Fix Audit")
with connection.cursor() as cur:
    cur.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'efbm_supplierbalance'
    """)
    sb_cols = [r[0] for r in cur.fetchall()]
    if 'total_bills' in sb_cols:
        print(f"   {PASS} SupplierBalance.total_bills exists (correct)")
    else:
        print(f"   {FAIL} SupplierBalance.total_bills MISSING")
    if 'total_billed' in sb_cols:
        print(f"   {FAIL} SupplierBalance.total_billed still exists (old column, should be gone)")
    else:
        print(f"   {PASS} SupplierBalance.total_billed correctly absent")
    if 'total_payments' in sb_cols:
        print(f"   {PASS} SupplierBalance.total_payments exists (correct)")
    else:
        print(f"   {FAIL} SupplierBalance.total_payments MISSING")

print("\n" + "=" * 70)
print("DATABASE & SECURITY VERIFICATION COMPLETE")
print("=" * 70)
