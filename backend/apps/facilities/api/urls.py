from django.urls import path
from backend.apps.facilities.api.views import (
    BuildingAPIView, RoomAPIView, WorkOrderAPIView
)

app_name = 'facilities_api'

urlpatterns = [
    path('buildings/', BuildingAPIView.as_view(), name='buildings'),
    path('rooms/', RoomAPIView.as_view(), name='rooms'),
    path('workorders/', WorkOrderAPIView.as_view(), name='workorders'),
]
