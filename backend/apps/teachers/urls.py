from django.urls import path, include
from django.views.generic import RedirectView
from backend.apps.teachers.views_web import TeacherDashboardWebView, WeeklyPlannerWebView

urlpatterns = [
    # Root redirect to dashboard
    path('', RedirectView.as_view(url='dashboard/', permanent=False)),
    # Web views
    path('dashboard/', TeacherDashboardWebView.as_view(), name='teacher_dashboard_web'),
    path('planner/', WeeklyPlannerWebView.as_view(), name='weekly_planner_web'),
    
    # API endpoints versions
    path('api/v1/', include('backend.apps.teachers.api.urls')),
]
