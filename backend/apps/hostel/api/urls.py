from django.urls import path
from backend.apps.hostel.api.views import (
    BedAllocationAPIView, HostelRollCallAPIView, HostelVisitorAPIView
)

app_name = 'hostel_api'

urlpatterns = [
    path('allocations/', BedAllocationAPIView.as_view(), name='allocations'),
    path('rollcall/', HostelRollCallAPIView.as_view(), name='rollcall'),
    path('visitor/', HostelVisitorAPIView.as_view(), name='visitor'),
]
