from django.urls import path
from backend.apps.emrp.api.views import (
    ExamResultAPIView, BroadsheetAPIView, PromotionsPreviewAPIView
)

app_name = 'emrp_api'

urlpatterns = [
    path('results/', ExamResultAPIView.as_view(), name='results'),
    path('exams/<uuid:exam_id>/broadsheet/', BroadsheetAPIView.as_view(), name='broadsheet'),
    path('promotions-preview/', PromotionsPreviewAPIView.as_view(), name='promotions_preview'),
]
