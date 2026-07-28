from django.urls import path, include
from django.views.generic import RedirectView
from backend.apps.attendance.views_web import AttendanceRegisterWebView, AttendanceDashboardWebView

urlpatterns = [
    # Root redirect to dashboard
    path('', RedirectView.as_view(url='dashboard/', permanent=False)),
    # Web views
    path('register/', AttendanceRegisterWebView.as_view(), name='attendance_register_web'),
    path('dashboard/', AttendanceDashboardWebView.as_view(), name='attendance_dashboard_web'),
    
    # API endpoints versions
    path('api/v1/', include('backend.apps.attendance.api.urls')),
]
