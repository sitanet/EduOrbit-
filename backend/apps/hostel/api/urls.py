from django.urls import path
from backend.apps.hostel.api.views import (
    HostelListAPIView, HostelApplicationAPIView, RoomAllocateAPIView, HostelOccupancyAPIView
)

app_name = 'hostel_api'

urlpatterns = [
    path('hostels/', HostelListAPIView.as_view(), name='hostel_list'),
    path('applications/', HostelApplicationAPIView.as_view(), name='hostel_application'),
    path('allocate/', RoomAllocateAPIView.as_view(), name='room_allocate'),
    path('occupancy/', HostelOccupancyAPIView.as_view(), name='hostel_occupancy'),
]
