"""
EduOrbit ERP v3.0.1 — Role Groups Seeder
==========================================
Creates Django Groups matching each role and assigns demo users.
Run once: python manage.py runscript seed_role_groups
Or: python backend/apps/dashboard/management/commands/seed_role_groups.py
"""
import os
import sys
import django

sys.path.insert(0, r'c:\Users\user\Desktop\Development\SMS')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings.local')
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()

# ─── Group definitions ────────────────────────────────────────────────────────
GROUPS = [
    'super_admin', 'school_admin', 'principal', 'vice_principal',
    'teacher', 'class_teacher',
    'student', 'parent', 'guardian',
    'finance_officer', 'bursar', 'accountant',
    'hr_admin', 'hr_officer', 'payroll_admin',
    'librarian', 'library_staff',
    'warden', 'hostel_officer',
    'transport_officer', 'transport_manager',
    'nurse', 'clinic_staff', 'doctor',
    'exam_officer', 'cbt_officer',
]

# ─── Demo user → Group assignments ───────────────────────────────────────────
DEMO_ASSIGNMENTS = {
    'admin.principal':   'school_admin',
    'teacher.john':      'teacher',
    'parent.david':      'parent',
    'student.romeo':     'student',
    'finance.officer':   'finance_officer',
    'hr.admin':          'hr_admin',
    'librarian.mary':    'librarian',
    'warden.sam':        'warden',
    'transport.officer': 'transport_officer',
    'nurse.sarah':       'nurse',
    'exam.officer':      'exam_officer',
    'payroll.admin':     'payroll_admin',
    'dept.manager':      'hr_officer',
}


def seed():
    print("=" * 60)
    print("  EduOrbit ERP v3.0.1 -- Role Groups Seeder")
    print("=" * 60)

    # 1. Create all groups
    for group_name in GROUPS:
        group, created = Group.objects.get_or_create(name=group_name)
        status = "CREATED" if created else "EXISTS "
        print(f"  [{status}] Group: {group_name}")

    print()
    print("  Assigning demo users to groups...")

    # 2. Assign demo users
    results = []
    for username, group_name in DEMO_ASSIGNMENTS.items():
        try:
            user = User.objects.get(username=username)
            group = Group.objects.get(name=group_name)

            # Remove from all OTHER groups first (clean slate)
            user.groups.clear()
            user.groups.add(group)

            # Ensure no demo user has is_superuser unless they are super.admin
            if username != 'super.admin':
                user.is_superuser = False
                user.is_staff = False
                user.save(update_fields=['is_superuser', 'is_staff'])

            results.append(f"  [OK] {username:<22} -> group: {group_name}")
        except User.DoesNotExist:
            results.append(f"  [--] {username:<22} -> user not found (skipped)")
        except Group.DoesNotExist:
            results.append(f"  [!!] {username:<22} -> group '{group_name}' not found")

    for r in results:
        print(r)

    print()
    print("=" * 60)
    print("  Seeding complete.")
    print("=" * 60)


if __name__ == '__main__':
    seed()
