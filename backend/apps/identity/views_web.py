from django.shortcuts import render, redirect
from django.views import View
from django.http import HttpResponse
from backend.apps.identity.services import IdentityService
from backend.apps.identity.models import UserSession, Role, Permission


def _get_post_login_url(user):
    """Return the correct dashboard URL based on the user's role."""
    if user.is_superuser:
        return '/administration/dashboard/'
    if user.is_staff:
        return '/tenants/tenant-dashboard/'
        
    # Check by database profile relationship
    if hasattr(user, 'person_profile') and user.person_profile:
        person = user.person_profile
        if hasattr(person, 'teacher_profile') and person.teacher_profile:
            return '/portal/teacher/'
        if hasattr(person, 'student_profile') and person.student_profile:
            return '/portal/student/'

    # Check by Django Group membership
    groups = list(user.groups.values_list('name', flat=True))
    if 'teacher' in groups or 'Teacher' in groups:
        return '/portal/teacher/'
    if 'student' in groups or 'Student' in groups:
        return '/portal/student/'
    if 'parent' in groups or 'Parent' in groups:
        return '/portal/parent/'
        
    # Fallback username matching for developer testing convenience
    uname = user.username.lower()
    if uname.startswith('teacher'):
        return '/portal/teacher/'
    if uname.startswith('student'):
        return '/portal/student/'
    if uname.startswith('parent'):
        return '/portal/parent/'
        
    # Default for school admin
    return '/portal/dashboard/'


class LoginWebView(View):
    def get(self, request):
        if request.GET.get('next') == 'logout':
            from django.contrib.auth import logout
            logout(request)
            return redirect('login_web')
            
        if request.user.is_authenticated:
            return redirect(_get_post_login_url(request.user))
        return render(request, 'identity/login.html')

    def post(self, request):
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        user = IdentityService.authenticate_user(
            credentials={"username": username, "password": password},
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

        if not user:
            return HttpResponse(
                '<div id="login-errors" style="color:#ef4444; padding:10px 14px; background:#fef2f2; '
                'border:1px solid #fecaca; border-radius:8px; margin-top:12px; font-size:14px;">'
                '&#x26A0; Invalid username or password. Please try again.</div>',
                status=401
            )

        from django.contrib.auth import login
        login(request, user)

        try:
            session = IdentityService.create_user_session(user=user)
            request.session['access_token'] = str(session.access_token_id)
        except Exception:
            pass  # Session tracking non-blocking

        redirect_url = _get_post_login_url(user)
        response = HttpResponse(status=200)
        response['HX-Redirect'] = redirect_url
        return response


class SessionManagementWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
        sessions = UserSession.objects.filter(user=request.user, revoked_at=None)
        return render(request, 'identity/sessions.html', {'sessions': sessions})


class RoleMatrixWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
        roles = Role.objects.all()
        permissions = Permission.objects.all()
        return render(request, 'identity/role_matrix.html', {'roles': roles, 'permissions': permissions})
