from django.urls import path
from backend.apps.students.api.views import (
    PlacementAPIView, PromotionAPIView, TimelineAPIView
)

app_name = 'students_api'

urlpatterns = [
    path('students/placements/', PlacementAPIView.as_view(), name='placements'),
    path('students/promotions/', PromotionAPIView.as_view(), name='promotions'),
    path('students/<uuid:student_id>/timeline/', TimelineAPIView.as_view(), name='timeline'),
]
