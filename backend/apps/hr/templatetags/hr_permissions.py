from django import template

register = template.Library()

@register.simple_tag
def has_hr_role(user, role_name):
    """
    Check if the authenticated user has a specific HR role name or superuser status.
    Supports: 'hr_admin', 'payroll_admin', 'supervisor', 'hr_officer', 'finance', 'employee'
    """
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser or getattr(user, 'is_staff', False):
        return True

    role_name = role_name.lower()
    
    # Check tenant memberships
    memberships = getattr(user, 'memberships', None)
    if memberships:
        for m in user.memberships.all():
            r_name = m.role.name.lower() if (m.role and m.role.name) else ""
            r_code = m.role.code.lower() if (m.role and m.role.code) else ""
            if role_name in r_name or role_name in r_code:
                return True
            if role_name == 'hr_admin' and any(k in r_name or k in r_code for k in ['admin', 'manager', 'director']):
                return True
            if role_name == 'supervisor' and any(k in r_name or k in r_code for k in ['supervisor', 'manager', 'lead', 'head']):
                return True
            if role_name == 'payroll_admin' and any(k in r_name or k in r_code for k in ['payroll', 'accountant', 'finance']):
                return True

    # Fallback to employee profile supervisor check
    if hasattr(user, 'person_profile') and hasattr(user.person_profile, 'employee_profile'):
        emp = user.person_profile.employee_profile
        if emp and role_name == 'supervisor' and emp.subordinates_history.filter(is_active=True).exists():
            return True

    return False

@register.simple_tag
def can_perform(user, permission_code):
    """
    Check granular permission code.
    """
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    
    # Check via user memberships and role permissions
    for m in user.memberships.all():
        if m.role and m.role.permissions.filter(code=permission_code).exists():
            return True
    return False

@register.simple_tag
def is_employee_self(user, employee_profile):
    """
    Check if employee_profile belongs to user.
    """
    if not user or not user.is_authenticated or not employee_profile:
        return False
    if hasattr(employee_profile, 'person') and employee_profile.person and employee_profile.person.user:
        return employee_profile.person.user == user
    return False
