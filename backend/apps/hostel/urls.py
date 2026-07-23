from django.urls import path, include
from backend.apps.hostel.views_web import HostelDashboardWebView, RoomsDirectoryWebView

urlpatterns = [
    # Web views
    path('dashboard/', HostelDashboardWebView.as_view(), name='hostel_dashboard_web'),
    path('rooms/', RoomsDirectoryWebView.as_view(), name='rooms_directory_web'),
    
    # API endpoints versions
    path('api/v1/', include('backend.apps.hostel.api.urls')),
]
