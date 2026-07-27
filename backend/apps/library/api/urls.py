from django.urls import path
from backend.apps.library.api.views import (
    BookListAPIView, BookCreateAPIView, BookIssueAPIView, BookReturnAPIView, FineListAPIView
)

app_name = 'library_api'

urlpatterns = [
    path('books/', BookListAPIView.as_view(), name='book_list'),
    path('books/create/', BookCreateAPIView.as_view(), name='book_create'),
    path('issues/', BookIssueAPIView.as_view(), name='book_issue'),
    path('returns/', BookReturnAPIView.as_view(), name='book_return'),
    path('fines/', FineListAPIView.as_view(), name='fine_list'),
]
