from backend.apps.hr.models.employee import EmployeeProfile

class HRContextMiddleware:
    """
    Middleware that inspects request.user and attaches HR context parameters:
    - request.hr_employee: EmployeeProfile instance for the current logged in user (or None)
    - request.hr_role: Main HR role string ('super_admin', 'hr_admin', 'payroll_admin', 'supervisor', 'hr_officer', 'employee')
    - request.is_supervisor: Boolean indicating if user has direct subordinates
    - request.hr_permissions: Set of active permission codes
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.hr_employee = None
        request.hr_role = 'employee'
        request.is_supervisor = False
        request.hr_permissions = set()

        if hasattr(request, 'user') and request.user.is_authenticated:
            user = request.user
            tenant = getattr(request, 'tenant', None)

            # Resolve Employee Profile
            try:
                if hasattr(user, 'person_profile') and user.person_profile:
                    request.hr_employee = EmployeeProfile.objects.filter(
                        person=user.person_profile
                    ).first()
                elif tenant:
                    request.hr_employee = EmployeeProfile.objects.filter(
                        tenant=tenant,
                        person__user=user
                    ).first()
            except Exception:
                request.hr_employee = None

            # Resolve Supervisor status
            if request.hr_employee:
                request.is_supervisor = request.hr_employee.subordinates_history.filter(is_active=True).exists()

            # Resolve Superuser / Admin role
            if user.is_superuser or getattr(user, 'is_staff', False):
                request.hr_role = 'hr_admin'
                request.is_supervisor = True
            else:
                # Fallback: Check username pattern for admin/principal users
                username_lower = user.username.lower()
                if any(keyword in username_lower for keyword in ['principal', 'school_admin', 'admin', 'vice_principal']):
                    request.hr_role = 'school_admin'
                    request.is_supervisor = True
                    print(f"DEBUG MIDDLEWARE: Set hr_role='school_admin' for user {user.username} based on username pattern")
                else:
                    # Check TenantMembership roles
                    memberships = user.memberships.filter(tenant=tenant) if tenant and hasattr(user, 'memberships') else []
                    print(f"DEBUG MIDDLEWARE: Found {len(memberships)} memberships for user {user.username}")
                    
                    for m in memberships:
                        r_name = m.role.name.lower() if (m.role and m.role.name) else ""
                        r_code = m.role.code.lower() if (m.role and m.role.code) else ""
                        print(f"DEBUG MIDDLEWARE: Role name='{r_name}', code='{r_code}'")
                        
                        # Check for admin-level roles (including school admin, principal, vice principal)
                        if any(k in r_name or k in r_code for k in ['admin', 'manager', 'director', 'principal', 'school_admin', 'vice_principal']):
                            request.hr_role = 'school_admin' if any(k in r_name or k in r_code for k in ['school_admin', 'principal', 'vice_principal']) else 'hr_admin'
                            print(f"DEBUG MIDDLEWARE: Set hr_role to '{request.hr_role}' based on role match")
                            break
                        elif any(k in r_name or k in r_code for k in ['payroll', 'accountant']):
                            request.hr_role = 'payroll_admin'
                        elif any(k in r_name or k in r_code for k in ['hr', 'officer']) and request.hr_role != 'payroll_admin':
                            request.hr_role = 'hr_officer'
                        elif any(k in r_name or k in r_code for k in ['supervisor', 'lead']) and request.hr_role == 'employee':
                            request.hr_role = 'supervisor'

                    if request.is_supervisor and request.hr_role == 'employee':
                        request.hr_role = 'supervisor'

            # Gather permissions
            if tenant and hasattr(user, 'memberships'):
                for m in user.memberships.filter(tenant=tenant):
                    if m.role:
                        codes = m.role.permissions.values_list('code', flat=True)
                        request.hr_permissions.update(codes)

        response = self.get_response(request)
        return response
