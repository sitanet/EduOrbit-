from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from backend.apps.tenants.models import Tenant, School
from backend.apps.people.models import Person
from backend.apps.library.models import Library, Book, BookCopy, BookIssue
from backend.apps.library.services.circulation import IssueBookService, ReturnBookService, FineCalculationService

class LibraryV150TestCase(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Library Tenant")
        self.school = School.objects.create(tenant=self.tenant, name="Alexandria International Academy")
        self.library = Library.objects.create(tenant=self.tenant, school=self.school, name="Main Central Library")
        self.borrower = Person.objects.create(
            tenant=self.tenant,
            person_number="PER-LIB-001",
            first_name="Eleanor",
            last_name="Vance",
            date_of_birth="2008-05-15",
            gender="female"
        )
        self.book = Book.objects.create(
            tenant=self.tenant,
            title="Principles of Quantum Physics",
            isbn="978-0134685991",
            category="Physics"
        )
        self.copy = BookCopy.objects.create(
            tenant=self.tenant,
            book=self.book,
            library=self.library,
            barcode="BC-PHY-998877",
            status="available",
            shelf_location="Aisle 4 - Shelf B"
        )
        self.client = APIClient()

    def test_circulation_issue_and_return_service_flow(self):
        # 1. Issue Book
        issue_res = IssueBookService.issue_book(borrower=self.borrower, copy=self.copy, duration_days=14)
        self.assertEqual(issue_res["status"], "success")
        self.copy.refresh_from_db()
        self.assertEqual(self.copy.status, "issued")
        issue = BookIssue.objects.get(id=issue_res["issue_id"])

        # 2. Return Book (No fine if on time)
        return_res = ReturnBookService.return_book(issue=issue)
        self.assertEqual(return_res["status"], "success")
        self.copy.refresh_from_db()
        self.assertEqual(self.copy.status, "available")
        self.assertEqual(return_res["fine_amount"], 0.00)

    def test_library_api_endpoints(self):
        # 1. Book List API
        list_url = '/library/api/v1/books/'
        resp = self.client.get(list_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data["count"] > 0)

        # 2. Issue Book API
        issue_url = '/library/api/v1/issues/'
        payload = {
            "borrower_id": str(self.borrower.id),
            "copy_id": str(self.copy.id),
            "duration_days": 7
        }
        issue_resp = self.client.post(issue_url, payload, format='json')
        self.assertEqual(issue_resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(issue_resp.data["status"], "success")
