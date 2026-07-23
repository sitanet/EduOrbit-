from django.urls import path, include
from backend.apps.hr.views_web import HRDashboardWebView, LeaveCalendarWebView, RecruitmentDashboardWebView, CandidateReviewWebView

urlpatterns = [
    # Web views
    path('dashboard/', HRDashboardWebView.as_view(), name='hr_dashboard_web'),
    path('leave-calendar/', LeaveCalendarWebView.as_view(), name='leave_calendar_web'),
    path('recruitment/', RecruitmentDashboardWebView.as_view(), name='recruitment_dashboard_web'),
    path('recruitment/candidate/<uuid:candidate_id>/review/', CandidateReviewWebView.as_view(), name='candidate_review_web'),
    
    # API endpoints versions
    path('api/v1/', include('backend.apps.hr.api.urls')),
]
