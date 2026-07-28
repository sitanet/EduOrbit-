from django.urls import path, include
from django.views.generic import RedirectView
from backend.apps.hostel.views_web import HostelDashboardWebView, RoomsDirectoryWebView

urlpatterns = [
    # Root redirect to dashboard
    path('', RedirectView.as_view(url='dashboard/', permanent=False)),
    # Web views
    path('dashboard/', HostelDashboardWebView.as_view(), name='hostel_dashboard_web'),
    path('rooms/', RoomsDirectoryWebView.as_view(), name='rooms_directory_web'),
    
    # API endpoints versions
    path('api/v1/', include('backend.apps.hostel.api.urls')),
]
