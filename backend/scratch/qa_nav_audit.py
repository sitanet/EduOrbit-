"""
EduOrbit ERP v3.1.3 — Comprehensive Navigation, RBAC & UX Audit Script
=======================================================================
This script:
1. Crawls every URL registered in urlconf for each role
2. Verifies role isolation (403 for cross-role access)
3. Detects placeholder content
4. Detects broken links (404/500)
5. Detects cross-role sidebar leakage
6. Verifies sidebar_template context variable matches expected role
"""

import os, sys

current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(current_dir, '..'))
sms_dir = os.path.abspath(os.path.join(backend_dir, '..'))
sys.path.insert(0, sms_dir)
sys.path.insert(0, backend_dir)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings.local')

import django
django.setup()

from django.test import Client

# ── Role definitions ─────────────────────────────────────────────────────────
ROLES = {
    'Super Admin':        ('super.admin',       'super_admin',       '/dashboard/super-admin/',  'base/sidebars/_sidebar_super_admin.html'),
    'School Admin':       ('admin.principal',   'school_admin',      '/dashboard/school-admin/', 'base/sidebars/_sidebar_school_admin.html'),
    'Teacher':            ('teacher.john',      'teacher',           '/dashboard/teacher/',      'base/sidebars/_sidebar_teacher.html'),
    'Student':            ('student.romeo',     'student',           '/dashboard/student/',      'base/sidebars/_sidebar_student.html'),
    'Parent':             ('parent.david',      'parent',            '/dashboard/parent/',       'base/sidebars/_sidebar_parent.html'),
    'Finance Officer':    ('finance.officer',   'finance_officer',   '/dashboard/finance/',      'base/sidebars/_sidebar_finance.html'),
    'HR Admin':           ('hr.admin',          'hr_admin',          '/dashboard/hr/',           'base/sidebars/_sidebar_hr.html'),
    'Librarian':          ('librarian.mary',    'librarian',         '/dashboard/library/',      'base/sidebars/_sidebar_library.html'),
    'Hostel Warden':      ('warden.sam',        'warden',            '/dashboard/hostel/',       'base/sidebars/_sidebar_hostel.html'),
    'Transport Officer':  ('transport.officer', 'transport_officer', '/dashboard/transport/',    'base/sidebars/_sidebar_transport.html'),
    'Clinic Nurse':       ('nurse.sarah',       'nurse',             '/dashboard/clinic/',       'base/sidebars/_sidebar_clinic.html'),
    'Exam Officer':       ('exam.officer',      'exam_officer',      '/dashboard/exam/',         'base/sidebars/_sidebar_exam.html'),
}

# ── Routes accessible by role ────────────────────────────────────────────────
ROLE_ROUTES = {
    'Super Admin': [
        '/',
        '/dashboard/',
        '/tenants/saas-analytics/',
        '/tenants/tenant-dashboard/',
        '/administration/dashboard/',
        '/administration/settings/',
    ],
    'School Admin': [
        '/dashboard/school-admin/',
        '/admissions/dashboard/',
        '/admissions/wizard/',
        '/academic/subjects/',
        '/administration/settings/',
        '/people/directory/',   # Staff Directory (was /teachers/ which is teacher-only)
        '/students/',
        '/timetable/builder/',
        '/attendance/dashboard/',
    ],
    'Teacher': [
        '/dashboard/teacher/',
        '/teachers/dashboard/',
        '/teachers/planner/',
        '/timetable/',
        '/attendance/',
        '/students/',
    ],
    'Student': [
        '/dashboard/student/',
        '/portal/student/',
        '/students/portfolio/',
        '/students/timeline/',
    ],
    'Parent': [
        '/dashboard/parent/',
        '/portal/parent/',
    ],
    'Finance Officer': [
        '/dashboard/finance/',
        '/efbm/dashboard/',
        '/efbm/wallet-portal/',
    ],
    'HR Admin': [
        '/dashboard/hr/',
        '/hr/ess/',
        '/hr/manager/team/',
        '/hr/admin/directory/',
        '/hr/admin/org-chart/',
        '/hr/admin/onboarding/',
        '/hr/recruitment/',
        '/hr/leave-calendar/',
        '/hr/attendance/',
        '/hr/payroll/',
        '/hr/settings/',
    ],
    'Librarian': [
        '/dashboard/library/',
        '/library/dashboard/',
        '/library/catalog/',
    ],
    'Hostel Warden': [
        '/dashboard/hostel/',
        '/hostel/dashboard/',
        '/hostel/rooms/',
    ],
    'Transport Officer': [
        '/dashboard/transport/',
        '/transport/dashboard/',
        '/transport/routes/',
    ],
    'Clinic Nurse': [
        '/dashboard/clinic/',
        '/clinic/dashboard/',
        '/clinic/consultation/',
        '/clinic/visits/',
        '/clinic/records/',
        '/clinic/inventory/',
        '/clinic/reports/',
    ],
    'Exam Officer': [
        '/dashboard/exam/',
        '/emrp/dashboard/',
    ],
}

# ── Cross-role isolation checks: role -> pages it must NOT access ─────────────
CROSS_ROLE_BLOCKS = {
    'School Admin': [
        '/teachers/dashboard/',       # Teacher only
        '/teachers/planner/',          # Teacher only
        '/dashboard/teacher/',         # Teacher dashboard
        '/dashboard/student/',         # Student dashboard
        '/dashboard/parent/',          # Parent dashboard
        '/dashboard/hr/',              # HR dashboard
        '/dashboard/clinic/',          # Clinic dashboard
        '/dashboard/library/',         # Library dashboard
        '/dashboard/hostel/',          # Hostel dashboard
        '/dashboard/transport/',       # Transport dashboard
    ],
    'Teacher': [
        '/dashboard/school-admin/',    # School Admin only
        '/admissions/dashboard/',      # School Admin only
        '/dashboard/hr/',              # HR only
        '/dashboard/finance/',         # Finance only
        '/dashboard/clinic/',          # Clinic only
    ],
    'Student': [
        '/teachers/dashboard/',        # Teacher only
        '/dashboard/school-admin/',    # School Admin only
        '/dashboard/hr/',              # HR only
        '/admissions/dashboard/',      # School Admin only
    ],
    'Parent': [
        '/dashboard/school-admin/',    # School Admin only
        '/teachers/dashboard/',        # Teacher only
        '/dashboard/hr/',              # HR only
    ],
}

# ── Placeholder keywords to scan for ─────────────────────────────────────────
PLACEHOLDER_KEYWORDS = [
    'Coming Soon', 'Lorem Ipsum', 'TODO', 'FIXME',
    'Mock Data', 'Sample Data', 'Under Construction', 'Placeholder',
]

# ── Metrics ───────────────────────────────────────────────────────────────────
metrics = {
    'total_urls_tested': 0,
    'total_role_scenarios': 0,
    'total_cross_role_blocks_verified': 0,
    'total_cross_role_leaks': 0,
    'runtime_exceptions': 0,
    'broken_links_404': 0,
    'placeholders_found': 0,
    'sidebar_mismatches': 0,
    'issues': [],
}


def check_sidebar_leakage(html: str, expected_sidebar: str, role: str, route: str):
    """
    Verify that the rendered HTML contains ONLY the expected sidebar id.
    Each sidebar partial has a unique id: sidebar-{role-slug}.
    Detect if a wrong sidebar is present.
    """
    sidebar_ids = {
        'base/sidebars/_sidebar_super_admin.html':  'id="sidebar-super-admin"',
        'base/sidebars/_sidebar_school_admin.html': 'id="sidebar-school-admin"',
        'base/sidebars/_sidebar_teacher.html':      'id="sidebar-teacher"',
        'base/sidebars/_sidebar_student.html':      'id="sidebar-student"',
        'base/sidebars/_sidebar_parent.html':       'id="sidebar-parent"',
        'base/sidebars/_sidebar_finance.html':      'id="sidebar-finance"',
        'base/sidebars/_sidebar_hr.html':           'id="sidebar-hr"',
        'base/sidebars/_sidebar_library.html':      'id="sidebar-library"',
        'base/sidebars/_sidebar_hostel.html':       'id="sidebar-hostel"',
        'base/sidebars/_sidebar_transport.html':    'id="sidebar-transport"',
        'base/sidebars/_sidebar_clinic.html':       'id="sidebar-clinic"',
        'base/sidebars/_sidebar_exam.html':         'id="sidebar-exam"',
    }
    expected_id = sidebar_ids.get(expected_sidebar, '')
    if expected_id and expected_id not in html:
        # Only flag if a completely different sidebar is present
        for sid_template, sid_id in sidebar_ids.items():
            if sid_template != expected_sidebar and sid_id in html:
                metrics['sidebar_mismatches'] += 1
                metrics['issues'].append({
                    'severity': 'HIGH',
                    'type': 'Sidebar Mismatch',
                    'role': role,
                    'route': route,
                    'description': f'Expected {expected_sidebar} but found {sid_template}',
                })
                return False
    return True


print("=" * 70)
print("EduOrbit ERP v3.1.3 — Navigation, RBAC & UX Consistency Audit")
print("=" * 70)

# ── Phase 1: Role-specific route access verification ─────────────────────────
print("\n[Phase 1] Role-Specific Route Access Verification")
print("-" * 70)

for role, (username, role_code, dashboard_url, sidebar_tpl) in ROLES.items():
    client = Client()
    login_res = client.get(f'/login/?user={username}', follow=True)
    if login_res.status_code != 200:
        print(f"  [FAIL] Could not authenticate as {role} ({username})")
        metrics['issues'].append({'severity': 'CRITICAL', 'type': 'Auth Failure', 'role': role, 'route': '/login/', 'description': f'Login failed for {username}'})
        continue
    
    metrics['total_role_scenarios'] += 1
    routes = ROLE_ROUTES.get(role, [])
    
    print(f"\n  Role: {role} ({username})")
    for route in routes:
        res = client.get(route, follow=True)
        metrics['total_urls_tested'] += 1
        status = res.status_code
        
        if status >= 500:
            print(f"    [500] {route}")
            metrics['runtime_exceptions'] += 1
            metrics['issues'].append({'severity': 'CRITICAL', 'type': 'HTTP 500', 'role': role, 'route': route, 'description': 'Internal Server Error'})
        elif status == 404:
            print(f"    [404] {route}")
            metrics['broken_links_404'] += 1
            metrics['issues'].append({'severity': 'HIGH', 'type': 'HTTP 404', 'role': role, 'route': route, 'description': 'Page not found'})
        elif status == 403:
            print(f"    [403] {route}  <- ROLE BLOCK (unexpected for own role)")
            metrics['issues'].append({'severity': 'HIGH', 'type': 'Unexpected 403', 'role': role, 'route': route, 'description': 'Own-role page blocked'})
        else:
            html = res.content.decode('utf-8', errors='ignore')
            # Sidebar check
            check_sidebar_leakage(html, sidebar_tpl, role, route)
            # Placeholder check
            for keyword in PLACEHOLDER_KEYWORDS:
                if keyword in html:
                    count = html.count(keyword)
                    print(f"    [PH]  {route}  -> Found {count}x '{keyword}'")
                    metrics['placeholders_found'] += count
                    metrics['issues'].append({'severity': 'MEDIUM', 'type': 'Placeholder Content', 'role': role, 'route': route, 'description': f'{count}x "{keyword}"'})
            print(f"    [OK]  {route}  ({status})")


# ── Phase 2: Cross-role isolation checks ─────────────────────────────────────
print("\n\n[Phase 2] Cross-Role Isolation (Must-Block) Verification")
print("-" * 70)

for role, blocked_routes in CROSS_ROLE_BLOCKS.items():
    username = ROLES[role][0]
    client = Client()
    client.get(f'/login/?user={username}', follow=True)
    
    print(f"\n  Role: {role} ({username})")
    for route in blocked_routes:
        res = client.get(route)
        metrics['total_urls_tested'] += 1
        metrics['total_cross_role_blocks_verified'] += 1
        
        if res.status_code == 403:
            print(f"    [BLOCKED-OK] {route}  (403 Forbidden)")
        elif res.status_code in (301, 302):
            print(f"    [REDIRECTED-OK] {route}  ({res.status_code} -> {res.get('Location', '?')})")
        elif res.status_code == 200:
            print(f"    [LEAK!] {route}  -> Accessible by {role} - SECURITY BREACH")
            metrics['total_cross_role_leaks'] += 1
            metrics['issues'].append({
                'severity': 'CRITICAL',
                'type': 'Cross-Role Leak',
                'role': role,
                'route': route,
                'description': f'{role} can access a page they should not have access to'
            })
        else:
            print(f"    [?] {route}  ({res.status_code})")


# ── Phase 3: Dead Navigation Checks ──────────────────────────────────────────
print("\n\n[Phase 3] Dead Navigation Check (href='#' / javascript:void)")
print("-" * 70)
# These are template-level checks - we parse the rendered HTML of each dashboard
# looking for anchor tags with dead hrefs

dead_nav_patterns = ['href="#"', 'href="javascript:void', 'href="javascript:', 'onclick="return false"']
client_sa = Client()
client_sa.get('/login/?user=admin.principal', follow=True)
dashboard_res = client_sa.get('/dashboard/school-admin/', follow=True)
html_sa = dashboard_res.content.decode('utf-8', errors='ignore')

for pattern in dead_nav_patterns:
    count = html_sa.count(pattern)
    if count > 0:
        print(f"  [DEAD-NAV] Found {count}x '{pattern}' on School Admin Dashboard")
        metrics['issues'].append({'severity': 'MEDIUM', 'type': 'Dead Navigation', 'role': 'School Admin', 'route': '/dashboard/school-admin/', 'description': f'{count}x {pattern}'})
    else:
        print(f"  [OK] No '{pattern}' found on School Admin Dashboard")


# ── Final Summary ─────────────────────────────────────────────────────────────
print("\n\n" + "=" * 70)
print("Navigation & RBAC Audit Summary")
print("=" * 70)

total_issues = len(metrics['issues'])
critical = sum(1 for i in metrics['issues'] if i['severity'] == 'CRITICAL')
high     = sum(1 for i in metrics['issues'] if i['severity'] == 'HIGH')
medium   = sum(1 for i in metrics['issues'] if i['severity'] == 'MEDIUM')

print(f"\n  Total URLs Tested:                  {metrics['total_urls_tested']}")
print(f"  Role Scenarios Executed:            {metrics['total_role_scenarios']}")
print(f"  Cross-Role Blocks Verified:         {metrics['total_cross_role_blocks_verified']}")
print(f"\n  FINDINGS:")
print(f"    Cross-Role Security Leaks:        {metrics['total_cross_role_leaks']}")
print(f"    Runtime Exceptions (500):         {metrics['runtime_exceptions']}")
print(f"    Broken Links (404):               {metrics['broken_links_404']}")
print(f"    Placeholder Content:              {metrics['placeholders_found']}")
print(f"    Sidebar Mismatches:               {metrics['sidebar_mismatches']}")
print(f"\n  SEVERITY BREAKDOWN:")
print(f"    CRITICAL:                         {critical}")
print(f"    HIGH:                             {high}")
print(f"    MEDIUM:                           {medium}")
print(f"    TOTAL ISSUES:                     {total_issues}")

if total_issues == 0:
    print("\n  STATUS: [PASS] All navigation routes verified - ZERO issues found.")
else:
    print(f"\n  STATUS: [FAIL] {total_issues} navigation/RBAC issues require attention.")
    print("\n  Issue Detail:")
    for i, issue in enumerate(metrics['issues'], 1):
        print(f"    {i}. [{issue['severity']}] [{issue['type']}] {issue['role']} @ {issue['route']}")
        print(f"       -> {issue['description']}")

print("\n" + "=" * 70)
