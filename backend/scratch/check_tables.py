import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings.local')
sys.path.insert(0, r'c:\Users\user\Desktop\Development\SMS')
import django; django.setup()
from backend.apps.hr.models import OnboardingDraft, EmployeeProfile
from django.db import connection

PASS = "PASS"
FAIL = "FAIL"

print("OnboardingDraft table:", OnboardingDraft._meta.db_table)
print("EmployeeProfile table:", EmployeeProfile._meta.db_table)

od_table = OnboardingDraft._meta.db_table
ep_table = EmployeeProfile._meta.db_table

with connection.cursor() as cur:
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = %s ORDER BY ordinal_position", [od_table])
    od_cols = [r[0] for r in cur.fetchall()]
    print(f"\nOnboardingDraft columns ({len(od_cols)}):", od_cols)

    # Check statutory fields in EmployeeProfile
    for field in ['nhf_number', 'nhis_number', 'nsitf_number', 'pfa_name', 'rsa_pin_encrypted']:
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = %s AND column_name = %s", [ep_table, field])
        found = cur.fetchone()
        print(f"  EmployeeProfile.{field}: {'[OK]' if found else '[MISSING]'}")

print("\nAll migrations applied:")
cur_check = connection.cursor()
cur_check.execute("SELECT app, name, applied FROM django_migrations WHERE app = 'hr' ORDER BY name")
for row in cur_check.fetchall():
    print(f"  [{row[0]}] {row[1]} applied={row[2]}")
