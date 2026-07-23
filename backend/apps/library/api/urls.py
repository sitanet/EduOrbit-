from django.urls import path
from backend.apps.library.api.views import (
    BookAPIView, BookIssueAPIView, DigitalResourceAPIView
)

app_name = 'library_api'

urlpatterns = [
    path('books/', BookAPIView.as_view(), name='books'),
    path('issues/', BookIssueAPIView.as_view(), name='issues'),
    path('digital/', DigitalResourceAPIView.as_view(), name='digital'),
]
