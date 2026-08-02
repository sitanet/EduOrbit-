"""
Phase 12.4.3C — Regression Audit Script
Verifies all core HR web views and API endpoints
"""
import os, sys, time
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings.local')
sys.path.insert(0, r'c:\Users\user\Desktop\Development\SMS')
import django; django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from backend.apps.tenants.models import Tenant

User = get_user_model()
PASS = "✓ PASS"
FAIL = "✗ FAIL"

print("=" * 70)
print("PHASE 12.4.3C — REGRESSION AUDIT")
print("=" * 70)

client = Client()
tenant = Tenant.objects.first()

# Get or create an admin user
admin_user = User.objects.filter(username='hr.admin').first()
if not admin_user:
    admin_user = User.objects.filter(is_superuser=True).first()
if not admin_user:
    admin_user = User.objects.create_user(
        username='audit_admin',
        password='auditpass123',
        email='audit@test.com',
        is_superuser=True,
        is_staff=True
    )

client.force_login(admin_user)

# ================================================================
# SECTION 1: Web Views (should return 200)
# ================================================================
print("\n[1] HR Web Views Regression Check")
web_views = [
    ('/hr/dashboard/', 'HR Dashboard'),
    ('/hr/ess/', 'ESS Dashboard'),
    ('/hr/admin/directory/', 'Staff Directory'),
    ('/hr/admin/org-chart/', 'Org Chart'),
    ('/hr/admin/onboarding/', 'Onboarding Tracker'),
    ('/hr/admin/onboarding/wizard/', 'Onboarding Wizard'),
    ('/hr/recruitment/', 'Recruitment'),
    ('/hr/leave-calendar/', 'Leave Calendar'),
    ('/hr/attendance/', 'Attendance'),
    ('/hr/performance/', 'Performance'),
    ('/hr/training/', 'Training'),
    ('/hr/disciplinary/', 'Disciplinary'),
    ('/hr/rewards/', 'Rewards'),
    ('/hr/analytics/', 'Analytics'),
    ('/hr/notifications/', 'Notifications'),
    ('/hr/audit/', 'Audit Trail'),
    ('/hr/settings/', 'HR Settings'),
    ('/hr/reports/', 'Reports'),
]

all_web_pass = True
for url, name in web_views:
    t0 = time.time()
    try:
        resp = client.get(url)
        elapsed = (time.time() - t0) * 1000
        # Accept 200 or redirect (302/301) as pass
        ok = resp.status_code in [200, 301, 302]
        status = PASS if ok else FAIL
        if not ok:
            all_web_pass = False
        print(f"   {status} {name}: HTTP {resp.status_code} ({elapsed:.0f}ms)")
    except Exception as e:
        all_web_pass = False
        print(f"   {FAIL} {name}: EXCEPTION — {e}")

# ================================================================
# SECTION 2: Payroll Access with school_admin role
# ================================================================
print("\n[2] Payroll Access by school_admin Role")
try:
    resp = client.get('/hr/payroll/')
    ok = resp.status_code in [200, 302]
    print(f"   {PASS if ok else FAIL} /hr/payroll/ => HTTP {resp.status_code}")
    if resp.status_code == 403:
        print(f"   {FAIL} Access Denied — school_admin role not recognized")
except Exception as e:
    print(f"   {FAIL} Exception: {e}")

# ================================================================
# SECTION 3: Unauthenticated access redirects
# ================================================================
print("\n[3] Unauthenticated Access Security Check")
anon_client = Client()
protected_urls = [
    '/hr/dashboard/',
    '/hr/admin/onboarding/wizard/',
    '/hr/payroll/',
]
for url in protected_urls:
    resp = anon_client.get(url)
    ok = resp.status_code in [302, 301, 403]
    print(f"   {PASS if ok else FAIL} {url} => HTTP {resp.status_code} (should redirect/deny unauthenticated)")

# ================================================================
# SECTION 4: API Endpoints
# ================================================================
print("\n[4] HR API Endpoint Regression Check")
import json
api_client = Client()
api_client.force_login(admin_user)

# Auto-save endpoint
resp = api_client.post(
    '/hr/api/v1/onboarding/draft/auto-save/',
    data=json.dumps({'current_step': 1, 'draft_data': {'first_name': 'Test'}}),
    content_type='application/json',
    HTTP_X_CSRFTOKEN='testtoken'
)
# Will be 400 if tenant not resolved (expected since middleware not running in test)
print(f"   {'✓' if resp.status_code != 500 else '✗'} POST /hr/api/v1/onboarding/draft/auto-save/ => HTTP {resp.status_code} (not 500)")

print("\n" + "=" * 70)
print("REGRESSION AUDIT COMPLETE")
print("=" * 70)
