from django.urls import path
from backend.apps.communication.api.views import (
    AnnouncementAPIView, NotificationAPIView, MessageAPIView
)

app_name = 'communication_api'

urlpatterns = [
    path('announcements/', AnnouncementAPIView.as_view(), name='announcements'),
    path('notifications/', NotificationAPIView.as_view(), name='notifications'),
    path('messages/', MessageAPIView.as_view(), name='messages'),
]
