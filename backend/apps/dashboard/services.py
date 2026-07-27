"""
EduOrbit ERP v3.0.1 — DashboardFactory Service
================================================
Resolves the correct dashboard for every authenticated user strictly from:
  - Django Groups
  - Django Permissions
  - Superuser status
  - TenantMembership roles

NEVER uses username, email, or URL-based role detection.
"""
from dataclasses import dataclass

# ─── Role Constants ───────────────────────────────────────────────────────────
ROLE_SUPER_ADMIN  = 'super_admin'
ROLE_SCHOOL_ADMIN = 'school_admin'
ROLE_TEACHER      = 'teacher'
ROLE_STUDENT      = 'student'
ROLE_PARENT       = 'parent'
ROLE_FINANCE      = 'finance_officer'
ROLE_HR           = 'hr_admin'
ROLE_LIBRARIAN    = 'librarian'
ROLE_WARDEN       = 'warden'
ROLE_TRANSPORT    = 'transport_officer'
ROLE_NURSE        = 'nurse'
ROLE_EXAM_OFFICER = 'exam_officer'


@dataclass
class DashboardSpec:
    role: str
    dashboard_url: str
    template: str
    sidebar_template: str
    dashboard_title: str
    accent_color: str


# ─── Dashboard Registry ───────────────────────────────────────────────────────
DASHBOARD_REGISTRY = {
    ROLE_SUPER_ADMIN: DashboardSpec(
        role=ROLE_SUPER_ADMIN,
        dashboard_url='/dashboard/super-admin/',
        template='dashboards/super_admin_dashboard.html',
        sidebar_template='base/sidebars/_sidebar_super_admin.html',
        dashboard_title='Platform Control Center',
        accent_color='indigo',
    ),
    ROLE_SCHOOL_ADMIN: DashboardSpec(
        role=ROLE_SCHOOL_ADMIN,
        dashboard_url='/dashboard/school-admin/',
        template='dashboards/school_admin_dashboard.html',
        sidebar_template='base/sidebars/_sidebar_school_admin.html',
        dashboard_title='School Administration Dashboard',
        accent_color='emerald',
    ),
    ROLE_TEACHER: DashboardSpec(
        role=ROLE_TEACHER,
        dashboard_url='/dashboard/teacher/',
        template='dashboards/teacher_dashboard.html',
        sidebar_template='base/sidebars/_sidebar_teacher.html',
        dashboard_title='Teacher Dashboard',
        accent_color='blue',
    ),
    ROLE_STUDENT: DashboardSpec(
        role=ROLE_STUDENT,
        dashboard_url='/dashboard/student/',
        template='dashboards/student_dashboard.html',
        sidebar_template='base/sidebars/_sidebar_student.html',
        dashboard_title='Student Portal',
        accent_color='violet',
    ),
    ROLE_PARENT: DashboardSpec(
        role=ROLE_PARENT,
        dashboard_url='/dashboard/parent/',
        template='dashboards/parent_dashboard.html',
        sidebar_template='base/sidebars/_sidebar_parent.html',
        dashboard_title='Parent Portal',
        accent_color='teal',
    ),
    ROLE_FINANCE: DashboardSpec(
        role=ROLE_FINANCE,
        dashboard_url='/dashboard/finance/',
        template='dashboards/finance_dashboard.html',
        sidebar_template='base/sidebars/_sidebar_finance.html',
        dashboard_title='Finance and Billing Dashboard',
        accent_color='amber',
    ),
    ROLE_HR: DashboardSpec(
        role=ROLE_HR,
        dashboard_url='/dashboard/hr/',
        template='dashboards/hr_dashboard.html',
        sidebar_template='base/sidebars/_sidebar_hr.html',
        dashboard_title='Human Resources Dashboard',
        accent_color='purple',
    ),
    ROLE_LIBRARIAN: DashboardSpec(
        role=ROLE_LIBRARIAN,
        dashboard_url='/dashboard/library/',
        template='dashboards/library_dashboard.html',
        sidebar_template='base/sidebars/_sidebar_library.html',
        dashboard_title='Library Management Dashboard',
        accent_color='amber',
    ),
    ROLE_WARDEN: DashboardSpec(
        role=ROLE_WARDEN,
        dashboard_url='/dashboard/hostel/',
        template='dashboards/hostel_dashboard.html',
        sidebar_template='base/sidebars/_sidebar_hostel.html',
        dashboard_title='Hostel Management Dashboard',
        accent_color='orange',
    ),
    ROLE_TRANSPORT: DashboardSpec(
        role=ROLE_TRANSPORT,
        dashboard_url='/dashboard/transport/',
        template='dashboards/transport_dashboard.html',
        sidebar_template='base/sidebars/_sidebar_transport.html',
        dashboard_title='Transport Management Dashboard',
        accent_color='sky',
    ),
    ROLE_NURSE: DashboardSpec(
        role=ROLE_NURSE,
        dashboard_url='/dashboard/clinic/',
        template='dashboards/clinic_dashboard.html',
        sidebar_template='base/sidebars/_sidebar_clinic.html',
        dashboard_title='School Clinic Dashboard',
        accent_color='rose',
    ),
    ROLE_EXAM_OFFICER: DashboardSpec(
        role=ROLE_EXAM_OFFICER,
        dashboard_url='/dashboard/exam/',
        template='dashboards/exam_dashboard.html',
        sidebar_template='base/sidebars/_sidebar_exam.html',
        dashboard_title='Examinations and Assessment Dashboard',
        accent_color='orange',
    ),
}


class DashboardFactory:
    """
    Resolves the correct dashboard for an authenticated user.
    Resolution order:
      1. is_superuser                  -> Super Admin
      2. Django Group membership        -> Role-specific
      3. TenantMembership role code     -> Role-specific
      4. Profile-based detection        -> Role-specific
      5. is_staff fallback              -> School Admin
    """

    GROUP_TO_ROLE = {
        'super_admin':       ROLE_SUPER_ADMIN,
        'school_admin':      ROLE_SCHOOL_ADMIN,
        'principal':         ROLE_SCHOOL_ADMIN,
        'vice_principal':    ROLE_SCHOOL_ADMIN,
        'teacher':           ROLE_TEACHER,
        'class_teacher':     ROLE_TEACHER,
        'student':           ROLE_STUDENT,
        'parent':            ROLE_PARENT,
        'guardian':          ROLE_PARENT,
        'finance_officer':   ROLE_FINANCE,
        'bursar':            ROLE_FINANCE,
        'accountant':        ROLE_FINANCE,
        'hr_admin':          ROLE_HR,
        'hr_officer':        ROLE_HR,
        'payroll_admin':     ROLE_HR,
        'librarian':         ROLE_LIBRARIAN,
        'library_staff':     ROLE_LIBRARIAN,
        'warden':            ROLE_WARDEN,
        'hostel_officer':    ROLE_WARDEN,
        'transport_officer': ROLE_TRANSPORT,
        'transport_manager': ROLE_TRANSPORT,
        'nurse':             ROLE_NURSE,
        'clinic_staff':      ROLE_NURSE,
        'doctor':            ROLE_NURSE,
        'exam_officer':      ROLE_EXAM_OFFICER,
        'cbt_officer':       ROLE_EXAM_OFFICER,
    }

    TENANT_ROLE_TO_ROLE = {
        'super_admin':  ROLE_SUPER_ADMIN,
        'school_admin': ROLE_SCHOOL_ADMIN,
        'teacher':      ROLE_TEACHER,
        'student':      ROLE_STUDENT,
        'parent':       ROLE_PARENT,
        'finance':      ROLE_FINANCE,
        'hr':           ROLE_HR,
        'librarian':    ROLE_LIBRARIAN,
        'warden':       ROLE_WARDEN,
        'transport':    ROLE_TRANSPORT,
        'nurse':        ROLE_NURSE,
        'exam_officer': ROLE_EXAM_OFFICER,
    }

    @classmethod
    def resolve_role(cls, user) -> str:
        """Determine the user's primary role — Groups/Permissions only, never username."""
        if user.is_superuser:
            return ROLE_SUPER_ADMIN

        user_groups = set(user.groups.values_list('name', flat=True))
        for group_name, role in cls.GROUP_TO_ROLE.items():
            if group_name in user_groups:
                return role

        if hasattr(user, 'memberships'):
            for membership in user.memberships.select_related('role').all():
                if membership.role and membership.role.code:
                    rc = membership.role.code.lower()
                    for key, role in cls.TENANT_ROLE_TO_ROLE.items():
                        if key in rc:
                            return role

        if hasattr(user, 'person_profile') and user.person_profile:
            person = user.person_profile
            if hasattr(person, 'student_profile') and person.student_profile:
                return ROLE_STUDENT
            if hasattr(person, 'teacher_profile') and person.teacher_profile:
                return ROLE_TEACHER

        if user.is_staff:
            return ROLE_SCHOOL_ADMIN

        return ROLE_SCHOOL_ADMIN

    @classmethod
    def get_spec(cls, user) -> DashboardSpec:
        role = cls.resolve_role(user)
        return DASHBOARD_REGISTRY.get(role, DASHBOARD_REGISTRY[ROLE_SCHOOL_ADMIN])

    @classmethod
    def get_dashboard_url(cls, user) -> str:
        return cls.get_spec(user).dashboard_url

    @classmethod
    def get_template(cls, user) -> str:
        return cls.get_spec(user).template

    @classmethod
    def get_sidebar_template(cls, user) -> str:
        return cls.get_spec(user).sidebar_template

    @classmethod
    def has_dashboard_access(cls, user, dashboard_role: str) -> bool:
        return cls.resolve_role(user) == dashboard_role or user.is_superuser

    @classmethod
    def get_context(cls, user) -> dict:
        spec = cls.get_spec(user)
        return {
            'dashboard_role':   spec.role,
            'dashboard_title':  spec.dashboard_title,
            'dashboard_url':    spec.dashboard_url,
            'sidebar_template': spec.sidebar_template,
            'accent_color':     spec.accent_color,
            'user_full_name':   user.get_full_name() or user.username,
        }
