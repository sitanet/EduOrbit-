from django.urls import path, include
from backend.apps.efbm.views_web import EFBMDashboardWebView, ParentWalletWebView

urlpatterns = [
    # Web views
    path('dashboard/', EFBMDashboardWebView.as_view(), name='efbm_dashboard_web'),
    path('wallet-portal/', ParentWalletWebView.as_view(), name='wallet_portal_web'),
    
    # API endpoints versions
    path('api/v1/', include('backend.apps.efbm.api.urls')),
]
