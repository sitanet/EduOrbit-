from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from backend.apps.library.models import Book, BookIssue, DigitalResource
from backend.apps.library.api.serializers import (
    BookSerializer, BookIssueSerializer, DigitalResourceSerializer
)
from backend.apps.core.events import event_bus, DomainEvent

class BookAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        query = request.query_params.get('q', '')
        if query:
            books = Book.objects.filter(tenant=request.tenant, title__icontains=query)
        else:
            books = Book.objects.filter(tenant=request.tenant)
        serializer = BookSerializer(books, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = BookSerializer(data=request.data)
        if serializer.is_valid():
            book = serializer.save(tenant=request.tenant)
            event_bus.publish(DomainEvent("book.cataloged", tenant_id=str(request.tenant.id), data={"id": str(book.id)}))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BookIssueAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        issues = BookIssue.objects.filter(tenant=request.tenant)
        serializer = BookIssueSerializer(issues, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = BookIssueSerializer(data=request.data)
        if serializer.is_valid():
            issue = serializer.save(tenant=request.tenant)
            event_bus.publish(DomainEvent("book.issued", tenant_id=str(request.tenant.id), data={"id": str(issue.id)}))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DigitalResourceAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        resources = DigitalResource.objects.filter(tenant=request.tenant)
        serializer = DigitalResourceSerializer(resources, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = DigitalResourceSerializer(data=request.data)
        if serializer.is_valid():
            res = serializer.save(tenant=request.tenant)
            event_bus.publish(DomainEvent("digital_resource.uploaded", tenant_id=str(request.tenant.id), data={"id": str(res.id)}))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
