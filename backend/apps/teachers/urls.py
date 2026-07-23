from django.urls import path, include
from backend.apps.teachers.views_web import TeacherDashboardWebView, WeeklyPlannerWebView

urlpatterns = [
    # Web views
    path('dashboard/', TeacherDashboardWebView.as_view(), name='teacher_dashboard_web'),
    path('planner/', WeeklyPlannerWebView.as_view(), name='weekly_planner_web'),
    
    # API endpoints versions
    path('api/v1/', include('backend.apps.teachers.api.urls')),
]
