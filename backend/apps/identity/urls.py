from django.urls import path, include
from backend.apps.identity.views_web import (
    LoginWebView, LogoutWebView, IdentityDashboardWebView, SessionManagementWebView, RoleMatrixWebView
)
from backend.apps.identity.views_demo import DemoCredentialsView

urlpatterns = [
    # Web views
    path('', IdentityDashboardWebView.as_view(), name='identity_root_web'),
    path('login/', LoginWebView.as_view(), name='login_web'),
    path('logout/', LogoutWebView.as_view(), name='logout_web'),
    path('sessions/', SessionManagementWebView.as_view(), name='sessions_web'),
    path('roles/', RoleMatrixWebView.as_view(), name='roles_web'),
    path('role-matrix/', RoleMatrixWebView.as_view(), name='role_matrix_web'),
    
    # Prefix Aliases
    path('identity/', IdentityDashboardWebView.as_view(), name='identity_prefix_root'),
    path('identity/sessions/', SessionManagementWebView.as_view(), name='identity_prefix_sessions'),
    path('identity/roles/', RoleMatrixWebView.as_view(), name='identity_prefix_roles'),
    path('identity/role-matrix/', RoleMatrixWebView.as_view(), name='identity_prefix_role_matrix'),
    
    path('demo-portal/', DemoCredentialsView.as_view(), name='demo_portal'),
    
    # API endpoints versions
    path('api/v1/', include('backend.apps.identity.api.urls')),
]
