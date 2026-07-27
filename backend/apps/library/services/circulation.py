from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from backend.apps.library.models import BookCopy, BookIssue, BorrowingPolicy
from backend.apps.efbm.services.accounting import JournalPostingService
from backend.apps.core.services.notifications import UnifiedNotificationService

class IssueBookService:
    """
    Circulation Book Checkout & Validation Engine.
    """
    @classmethod
    @transaction.atomic
    def issue_book(cls, borrower, copy, duration_days=14):
        tenant = borrower.tenant

        if copy.status != 'available':
            return {
                "status": "error",
                "message": f"Book copy #{copy.barcode} is not available (Current status: {copy.status})."
            }

        due_date = timezone.now().date() + timezone.timedelta(days=duration_days)

        # 1. Update Copy Status
        copy.status = 'issued'
        copy.save()

        # 2. Create Issue Checkout Record
        issue = BookIssue.objects.create(
            tenant=tenant,
            copy=copy,
            borrower=borrower,
            issue_date=timezone.now().date(),
            due_date=due_date,
            status='issued'
        )

        # 3. Dispatch Circulation Notification
        UnifiedNotificationService.send_notification(
            recipient=borrower.first_name,
            title="Book Checked Out",
            message=f"Book '{copy.book.title}' (Barcode: {copy.barcode}) checked out. Due date: {due_date}.",
            channels=['in_app', 'email']
        )

        return {
            "status": "success",
            "issue_id": str(issue.id),
            "barcode": copy.barcode,
            "book_title": copy.book.title,
            "borrower_name": borrower.first_name,
            "due_date": str(due_date)
        }


class ReturnBookService:
    """
    Book Return & Fine Assessment Engine with General Ledger Integration.
    """
    @classmethod
    @transaction.atomic
    def return_book(cls, issue):
        tenant = issue.tenant
        return_date = timezone.now().date()

        fine_amt = Decimal('0.00')
        if return_date > issue.due_date:
            overdue_days = (return_date - issue.due_date).days
            fine_amt = Decimal(str(overdue_days * 5.00))  # $5 per overdue day

        # 1. Update Book Issue
        issue.return_date = return_date
        issue.fine_amount = fine_amt
        issue.status = 'returned'
        issue.save()

        # 2. Update Copy Status to Available
        copy = issue.copy
        copy.status = 'available'
        copy.save()

        # 3. GL Accounting Integration if fine imposed
        if fine_amt > Decimal('0.00') and hasattr(issue.borrower, 'school') and issue.borrower.school:
            JournalPostingService.post_journal_entry(
                school=issue.borrower.school,
                event_type="library_fine",
                debit_account="Library Fines Receivable",
                credit_account="Library Fine Revenue",
                amount=fine_amt
            )

        return {
            "status": "success",
            "issue_id": str(issue.id),
            "barcode": copy.barcode,
            "return_date": str(return_date),
            "fine_amount": float(fine_amt),
            "copy_status": copy.status
        }


class FineCalculationService:
    """
    Overdue Daily Penalty Calculation Service.
    """
    @classmethod
    def calculate_fine(cls, issue):
        today = timezone.now().date()
        if today <= issue.due_date:
            return {"overdue_days": 0, "fine_amount": 0.00}

        overdue_days = (today - issue.due_date).days
        fine_amt = float(overdue_days * 5.00)
        return {"overdue_days": overdue_days, "fine_amount": fine_amt}
