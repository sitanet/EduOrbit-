from django.urls import path, include
from backend.apps.portal.views_web import (
    PortalDashboardWebView, ParentDashboardWebView, StudentDashboardWebView, TeacherDashboardWebView
)

urlpatterns = [
    # Web views
    path('dashboard/', PortalDashboardWebView.as_view(), name='portal_dashboard_web'),
    path('parent/', ParentDashboardWebView.as_view(), name='parent_dashboard_web'),
    path('student/', StudentDashboardWebView.as_view(), name='student_dashboard_web'),
    path('teacher/', TeacherDashboardWebView.as_view(), name='teacher_dashboard_web'),
    
    # API endpoints versions
    path('api/v1/', include('backend.apps.portal.api.urls')),
]
