from django.urls import path, include
from django.views.generic import RedirectView
from backend.apps.communication.views_web import CEHDashboardWebView, ChatWebView

urlpatterns = [
    # Root redirect to dashboard
    path('', RedirectView.as_view(url='dashboard/', permanent=False)),
    # Web views
    path('dashboard/', CEHDashboardWebView.as_view(), name='ceh_dashboard_web'),
    path('chat-room/', ChatWebView.as_view(), name='chat_room_web'),
    
    # API endpoints versions
    path('api/v1/', include('backend.apps.communication.api.urls')),
]
