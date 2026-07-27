from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from backend.apps.people.models import Person
from backend.apps.library.models import Book, BookCopy, BookIssue
from backend.apps.library.services.circulation import IssueBookService, ReturnBookService, FineCalculationService

class BookListAPIView(APIView):
    def get(self, request):
        books = Book.objects.all()
        data = [
            {
                "id": str(b.id),
                "title": b.title,
                "isbn": b.isbn,
                "category": b.category,
                "language": b.language,
                "copies_count": b.copies.count()
            }
            for b in books
        ]
        return Response({"status": "success", "count": len(data), "data": data})


class BookCreateAPIView(APIView):
    def post(self, request):
        title = request.data.get('title')
        isbn = request.data.get('isbn', '')
        category = request.data.get('category', 'General')
        person_id = request.data.get('person_id')

        try:
            person = Person.objects.get(id=person_id) if person_id else Person.objects.first()
            book = Book.objects.create(
                tenant=person.tenant,
                title=title,
                isbn=isbn,
                category=category
            )
            return Response({
                "status": "success",
                "data": {"id": str(book.id), "title": book.title, "isbn": book.isbn}
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class BookIssueAPIView(APIView):
    def post(self, request):
        borrower_id = request.data.get('borrower_id')
        copy_id = request.data.get('copy_id')
        duration_days = request.data.get('duration_days', 14)

        try:
            borrower = Person.objects.get(id=borrower_id)
            copy = BookCopy.objects.get(id=copy_id)
            res = IssueBookService.issue_book(borrower=borrower, copy=copy, duration_days=duration_days)
            return Response({"status": "success" if res["status"] == "success" else "error", "data": res}, status=status.HTTP_201_CREATED if res["status"] == "success" else status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class BookReturnAPIView(APIView):
    def post(self, request):
        issue_id = request.data.get('issue_id')

        try:
            issue = BookIssue.objects.get(id=issue_id)
            res = ReturnBookService.return_book(issue=issue)
            return Response({"status": "success", "data": res}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class FineListAPIView(APIView):
    def get(self, request):
        issues = BookIssue.objects.filter(fine_amount__gt=0.00)
        data = [
            {
                "issue_id": str(i.id),
                "barcode": i.copy.barcode,
                "borrower": i.borrower.person_number,
                "fine_amount": float(i.fine_amount),
                "status": i.status
            }
            for i in issues
        ]
        return Response({"status": "success", "count": len(data), "data": data})
