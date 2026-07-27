from django.urls import path
from backend.apps.portal.api.views import (
    ParentDashboardAPIView, StudentDashboardAPIView, StaffDashboardAPIView, PortalProfileAPIView
)

app_name = 'portal_api'

urlpatterns = [
    path('parent/dashboard/', ParentDashboardAPIView.as_view(), name='parent_dashboard'),
    path('student/dashboard/', StudentDashboardAPIView.as_view(), name='student_dashboard'),
    path('staff/dashboard/', StaffDashboardAPIView.as_view(), name='staff_dashboard'),
    path('profile/', PortalProfileAPIView.as_view(), name='portal_profile'),
]
