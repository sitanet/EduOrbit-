from django.urls import path, include
from backend.apps.communication.views_web import CEHDashboardWebView, ChatWebView

urlpatterns = [
    # Web views
    path('dashboard/', CEHDashboardWebView.as_view(), name='ceh_dashboard_web'),
    path('chat-room/', ChatWebView.as_view(), name='chat_room_web'),
    
    # API endpoints versions
    path('api/v1/', include('backend.apps.communication.api.urls')),
]
