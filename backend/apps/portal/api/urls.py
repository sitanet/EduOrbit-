from django.urls import path
from backend.apps.portal.api.views import (
    PortalProfileAPIView, PortalNotificationAPIView, PortalShortcutAPIView
)

app_name = 'portal_api'

urlpatterns = [
    path('profile/', PortalProfileAPIView.as_view(), name='profile'),
    path('notifications/', PortalNotificationAPIView.as_view(), name='notifications'),
    path('shortcuts/', PortalShortcutAPIView.as_view(), name='shortcuts'),
]
