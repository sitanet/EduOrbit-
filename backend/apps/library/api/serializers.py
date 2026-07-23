from rest_framework import serializers
from backend.apps.library.models import (
    Library, Author, Publisher, Book, BookCopy, BorrowingPolicy, BookIssue, BookReservation, DigitalResource, ReadingChallenge, ReadingProgress
)

class LibrarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Library
        fields = ['id', 'school', 'name', 'location']


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ['id', 'name', 'biography']


class PublisherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Publisher
        fields = ['id', 'name', 'address']


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ['id', 'title', 'authors', 'publisher', 'isbn', 'category', 'subject', 'language']


class BookCopySerializer(serializers.ModelSerializer):
    class Meta:
        model = BookCopy
        fields = ['id', 'book', 'library', 'barcode', 'status', 'shelf_location']


class PolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = BorrowingPolicy
        fields = ['id', 'role_code', 'max_books', 'loan_duration_days', 'fine_per_day']


class BookIssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookIssue
        fields = ['id', 'copy', 'borrower', 'issue_date', 'due_date', 'return_date', 'fine_amount', 'status']


class BookReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookReservation
        fields = ['id', 'book', 'borrower', 'request_date', 'status']


class DigitalResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DigitalResource
        fields = ['id', 'title', 'file_url', 'resource_type', 'download_limit']
