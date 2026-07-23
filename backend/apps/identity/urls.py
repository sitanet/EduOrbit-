from django.urls import path, include
from backend.apps.identity.views_web import LoginWebView, SessionManagementWebView, RoleMatrixWebView

urlpatterns = [
    # Web views
    path('login/', LoginWebView.as_view(), name='login_web'),
    path('sessions/', SessionManagementWebView.as_view(), name='sessions_web'),
    path('roles/', RoleMatrixWebView.as_view(), name='roles_web'),
    
    # API endpoints versions
    path('api/v1/', include('backend.apps.identity.api.urls')),
]
