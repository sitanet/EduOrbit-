"""
EduOrbit ERP v3.0.1 — Permission Context Processor
====================================================
Injects role-scoped context variables into every template context:
  - sidebar_template  → path to the role-isolated sidebar partial
  - dashboard_role    → string role identifier (e.g. 'teacher')
  - dashboard_title   → human-readable dashboard name
  - dashboard_url     → canonical home URL for the user's role
  - accent_color      → role branding colour
  - user_full_name    → full name or username

Called once per request. All values come from DashboardFactory which
resolves from Django Groups / Superuser only — never username strings.
"""
from backend.apps.dashboard.services import DashboardFactory


def permission_context(request):
    """
    Global context processor: inject role & sidebar variables into all templates.
    Returns empty dict for anonymous users (no overhead).
    """
    if not request.user.is_authenticated:
        return {
            'sidebar_template': None,
            'dashboard_role': None,
            'dashboard_title': '',
            'dashboard_url': '/',
            'accent_color': 'indigo',
            'user_full_name': '',
        }

    try:
        ctx = DashboardFactory.get_context(request.user)
        return ctx
    except Exception:
        # Never let a context processor crash a page render
        return {
            'sidebar_template': 'base/sidebars/_sidebar_school_admin.html',
            'dashboard_role': 'school_admin',
            'dashboard_title': 'Dashboard',
            'dashboard_url': '/dashboard/',
            'accent_color': 'emerald',
            'user_full_name': getattr(request.user, 'username', ''),
        }
