import os
import sys

backend_dir = r"c:\Users\user\Desktop\Development\SMS\backend"
sms_dir = r"c:\Users\user\Desktop\Development\SMS"
sys.path.insert(0, sms_dir)
sys.path.insert(0, backend_dir)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings.local')

import django
django.setup()

from django.urls import get_resolver, URLPattern, URLResolver
from django.test import Client

# User roles to test against
ROLES = {
    'Super Admin':       ('super.admin',       'super_admin'),
    'School Admin':      ('admin.principal',   'school_admin'),
    'Teacher':           ('teacher.john',      'teacher'),
    'Student':           ('student.romeo',     'student'),
    'Parent':            ('parent.david',      'parent'),
    'Finance Officer':   ('finance.officer',   'finance_officer'),
    'HR Admin':          ('hr.admin',          'hr_admin'),
    'Librarian':         ('librarian.mary',    'librarian'),
    'Hostel Warden':     ('warden.sam',        'warden'),
    'Transport Officer': ('transport.officer', 'transport_officer'),
    'Clinic Nurse':      ('nurse.sarah',       'nurse'),
    'Exam Officer':      ('exam.officer',      'exam_officer'),
}

all_url_patterns = []

def clean_pattern_str(s):
    # Remove regex markers
    return s.replace('^', '').replace('$', '').replace('\\', '')

def extract_patterns(patterns, prefix=""):
    for item in patterns:
        if isinstance(item, URLPattern):
            raw_path = clean_pattern_str(str(item.pattern))
            full_path = prefix + raw_path
            if not full_path.startswith('/'):
                full_path = '/' + full_path
            all_url_patterns.append((full_path, item))
        elif isinstance(item, URLResolver):
            sub_prefix = prefix + clean_pattern_str(str(item.pattern))
            extract_patterns(item.url_patterns, sub_prefix)

resolver = get_resolver()
extract_patterns(resolver.url_patterns)

print(f"Extracted {len(all_url_patterns)} registered URL patterns from URLconf.")

route_audit = []

for clean_url, pattern_obj in all_url_patterns:
    is_parameterized = '<' in clean_url or '(' in clean_url or '?' in clean_url
    
    view_func = pattern_obj.callback
    view_name = getattr(view_func, '__name__', str(view_func))
    view_module = getattr(view_func, '__module__', 'unknown')
    
    responses_by_role = {}
    # Audit static web endpoints (excluding django admin and raw rest api endpoints)
    if not is_parameterized and not clean_url.startswith('/admin/') and not clean_url.startswith('/api/') and 'api/' not in clean_url:
        for role_name, (username, role_code) in ROLES.items():
            client = Client()
            client.get(f'/login/?user={username}', follow=True)
            res = client.get(clean_url)
            responses_by_role[role_name] = res.status_code

    route_audit.append({
        'url': clean_url,
        'view_name': view_name,
        'view_module': view_module,
        'is_parameterized': is_parameterized,
        'responses': responses_by_role
    })

import json
with open(os.path.join(backend_dir, "scratch", "urlconf_rbac_audit.json"), "w") as out:
    json.dump(route_audit, out, indent=2)

print(f"Audited {len(route_audit)} routes.")
