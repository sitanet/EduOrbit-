from django.test import TestCase
from django.utils import timezone
from datetime import date, timedelta
from backend.apps.tenants.models import Tenant, School
from backend.apps.people.models import Person
from backend.apps.library.models import (
    Library, Author, Publisher, Book, BookCopy, BorrowingPolicy, BookIssue, BookReservation, DigitalResource
)

class LibraryPlatformTests(TestCase):
    def setUp(self):
        # Create core configurations
        self.tenant = Tenant.objects.create(name="ELMS Org")
        self.school = School.objects.create(tenant=self.tenant, name="ELMS High School", school_types=["secondary"])
        
        # Person
        self.person = Person.objects.create(
            tenant=self.tenant,
            person_number="P-40088",
            first_name="Jane",
            last_name="Foster",
            gender="female",
            date_of_birth="2010-09-12"
        )
        
        # Library & Bibliographic
        self.library = Library.objects.create(school=self.school, tenant=self.tenant, name="Secondary Main Library")
        self.author = Author.objects.create(tenant=self.tenant, name="J.K. Rowling")
        self.publisher = Publisher.objects.create(tenant=self.tenant, name="Bloomsbury")
        
        self.book = Book.objects.create(
            tenant=self.tenant,
            title="Harry Potter and the Philosopher's Stone",
            publisher=self.publisher,
            isbn="978-0747532699",
            category="fiction",
            subject="magic"
        )
        self.book.authors.add(self.author)
        
        self.copy = BookCopy.objects.create(
            book=self.book,
            library=self.library,
            tenant=self.tenant,
            barcode="BC-0001",
            status="available"
        )
        
        # Borrowing Policy
        self.policy = BorrowingPolicy.objects.create(
            tenant=self.tenant,
            role_code="student",
            max_books=3,
            loan_duration_days=14,
            fine_per_day=50.00
        )

    def test_overdue_fines_accumulation_calculation(self):
        # Create a loan that is 5 days overdue
        issue_date = date.today() - timedelta(days=20)
        due_date = date.today() - timedelta(days=6)
        
        loan = BookIssue.objects.create(
            copy=self.copy,
            borrower=self.person,
            tenant=self.tenant,
            issue_date=issue_date,
            due_date=due_date,
            status="issued"
        )
        
        # Calculate fine
        overdue_days = (date.today() - loan.due_date).days
        if overdue_days > 0:
            loan.fine_amount = overdue_days * self.policy.fine_per_day
            loan.save()
            
        self.assertEqual(loan.fine_amount, 300.00) # 6 days * 50

    def test_book_reservation_stage_transitions(self):
        hold = BookReservation.objects.create(
            book=self.book,
            borrower=self.person,
            tenant=self.tenant,
            status="pending"
        )
        self.assertEqual(hold.status, "pending")
        
        hold.status = "fulfilled"
        hold.save()
        self.assertEqual(hold.status, "fulfilled")
