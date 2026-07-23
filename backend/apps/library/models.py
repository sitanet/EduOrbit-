import uuid
from django.db import models
from django.utils import timezone
from backend.apps.core.models import TenantBaseModel, PlatformBaseModel

# ==============================================================
# BIBLIOGRAPHIC CATALOG
# ==============================================================

class Library(TenantBaseModel):
    """
    Physical library buildings, branches, or rooms within campuses.
    """
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE)
    name = models.CharField(max_length=150)
    location = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return self.name


class Author(TenantBaseModel):
    name = models.CharField(max_length=150)
    biography = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Publisher(TenantBaseModel):
    name = models.CharField(max_length=150)
    address = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Book(TenantBaseModel):
    """
    Bibliographical title definition (OPAC record base).
    """
    title = models.CharField(max_length=200)
    authors = models.ManyToManyField(Author, related_name='books')
    publisher = models.ForeignKey(Publisher, on_delete=models.SET_NULL, null=True, blank=True, related_name='books')
    isbn = models.CharField(max_length=50, blank=True)
    category = models.CharField(max_length=100, blank=True)
    subject = models.CharField(max_length=100, blank=True)
    language = models.CharField(max_length=50, default='english')

    def __str__(self):
        return self.title


class BookCopy(TenantBaseModel):
    """
    Physical copy tracker holding unique barcode identifiers.
    """
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('issued', 'Issued'),
        ('lost', 'Lost'),
        ('damaged', 'Damaged')
    ]
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='copies')
    library = models.ForeignKey(Library, on_delete=models.CASCADE, related_name='copies')
    barcode = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='available')
    shelf_location = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"{self.book.title} (Copy: {self.barcode})"


# ==============================================================
# CIRCULATION & POLICIES RULES
# ==============================================================

class BorrowingPolicy(TenantBaseModel):
    """
    Saves limits configuration arrays scoped to roles (primary/sec student, teacher).
    """
    role_code = models.CharField(max_length=50)  # student, teacher
    max_books = models.IntegerField(default=3)
    loan_duration_days = models.IntegerField(default=14)
    fine_per_day = models.DecimalField(max_digits=8, decimal_places=2, default=50.00)

    def __str__(self):
        return f"Policy: {self.role_code} (Max: {self.max_books} books)"


class BookIssue(TenantBaseModel):
    """
    Circulation borrow checkouts tracking.
    """
    STATUS_CHOICES = [
        ('issued', 'Issued'),
        ('returned', 'Returned'),
        ('lost', 'Lost')
    ]
    copy = models.ForeignKey(BookCopy, on_delete=models.CASCADE, related_name='issues')
    borrower = models.ForeignKey('people.Person', on_delete=models.CASCADE, related_name='library_loans')
    issue_date = models.DateField(default=timezone.now)
    due_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    fine_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='issued')

    def __str__(self):
        return f"{self.copy.barcode} borrowed by {self.borrower.person_number}"


class BookReservation(TenantBaseModel):
    """
    Queue management holds.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('fulfilled', 'Fulfilled'),
        ('cancelled', 'Cancelled')
    ]
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reservations')
    borrower = models.ForeignKey('people.Person', on_delete=models.CASCADE, related_name='library_holds')
    request_date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"Hold: {self.book.title} for {self.borrower.person_number}"


# ==============================================================
# DIGITAL LIBRARY & LITERACY CHALLENGES
# ==============================================================

class DigitalResource(TenantBaseModel):
    title = models.CharField(max_length=200)
    file_url = models.CharField(max_length=255, blank=True)
    resource_type = models.CharField(max_length=50, default='pdf')  # ebook, journal_pdf, interactive
    download_limit = models.IntegerField(default=0)  # 0 indicates unlimited

    def __str__(self):
        return self.title


class ReadingChallenge(TenantBaseModel):
    title = models.CharField(max_length=150)
    target_books_count = models.IntegerField(default=5)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.title


class ReadingProgress(TenantBaseModel):
    student = models.ForeignKey('people.Person', on_delete=models.CASCADE, related_name='reading_progress')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reading_progress')
    pages_read = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.student.person_number} progress on {self.book.title}"
