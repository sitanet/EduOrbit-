from django.urls import path, include
from django.views.generic import RedirectView
from backend.apps.efbm.views_web import EFBMDashboardWebView, ParentWalletWebView

urlpatterns = [
    # Root redirect to dashboard
    path('', RedirectView.as_view(url='dashboard/', permanent=False)),
    # Web views
    path('dashboard/', EFBMDashboardWebView.as_view(), name='efbm_dashboard_web'),
    path('wallet-portal/', ParentWalletWebView.as_view(), name='wallet_portal_web'),
    
    # API endpoints versions
    path('api/v1/', include('backend.apps.efbm.api.urls')),
]
