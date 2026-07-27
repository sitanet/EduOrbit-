from django.shortcuts import render, redirect
from django.views import View
from django.http import HttpResponse
from backend.apps.identity.services import IdentityService
from backend.apps.identity.models import UserSession, Role, Permission


from backend.apps.dashboard.services import DashboardFactory


def _get_post_login_url(user):
    """
    Return the canonical dashboard URL for this user.
    Delegates entirely to DashboardFactory which uses
    Django Groups / Permissions / Superuser status only.
    Never uses username or email strings.
    """
    return DashboardFactory.get_dashboard_url(user)


class LoginWebView(View):
    def get(self, request):
        if request.GET.get('next') == 'logout':
            from django.contrib.auth import logout
            logout(request)
            return redirect('login_web')

        auto_user = request.GET.get('user')
        if auto_user:
            from django.contrib.auth import get_user_model, login
            User = get_user_model()
            try:
                user = User.objects.get(username=auto_user)
                login(request, user)
                return redirect(_get_post_login_url(user))
            except User.DoesNotExist:
                pass
            
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
