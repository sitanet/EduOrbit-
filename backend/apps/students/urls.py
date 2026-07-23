from django.urls import path, include
from backend.apps.students.views_web import StudentPortfolioWebView, StudentTimelineWebView

urlpatterns = [
    # Web views
    path('portfolio/', StudentPortfolioWebView.as_view(), name='portfolio_list_web'),
    path('timeline/', StudentTimelineWebView.as_view(), name='timeline_log_web'),
    
    # API endpoints versions
    path('api/v1/', include('backend.apps.students.api.urls')),
]
