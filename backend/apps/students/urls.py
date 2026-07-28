from django.urls import path, include
from django.views.generic import RedirectView
from backend.apps.students.views_web import StudentPortfolioWebView, StudentTimelineWebView

urlpatterns = [
    # Root redirect to portfolio
    path('', RedirectView.as_view(url='portfolio/', permanent=False)),
    # Web views
    path('portfolio/', StudentPortfolioWebView.as_view(), name='portfolio_list_web'),
    path('timeline/', StudentTimelineWebView.as_view(), name='timeline_log_web'),
    
    # API endpoints versions
    path('api/v1/', include('backend.apps.students.api.urls')),
]
