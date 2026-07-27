from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import get_user_model, login

User = get_user_model()

class DemoCredentialsView(View):
    """
    Web-based Role Credentials & Auto-Login Hub for EduOrbit ERP.
    """
    def get(self, request):
        user_param = request.GET.get('auto_login')
        if user_param:
            try:
                user = User.objects.get(username=user_param)
                login(request, user)
                from backend.apps.identity.views_web import _get_post_login_url
                return redirect(_get_post_login_url(user))
            except User.DoesNotExist:
                pass
        return render(request, 'identity/demo_portal.html')
