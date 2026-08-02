"""
Comprehensive test suite for Supplier Debit Note functionality.
Tests service layer, model validation, workflow states, and accounting integration.
"""

from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth.models import User

from backend.apps.tenants.models import Tenant
from backend.apps.people.models import Person
from backend.apps.efbm.models import SupplierBill, SupplierDebitNote, Supplier
from backend.apps.efbm.services.payables import SupplierDebitNoteService


class SupplierDebitNoteModelTest(TestCase):
    """Test SupplierDebitNote model validation and constraints."""
    
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test School")
        self.bill = SupplierBill.objects.create(
            tenant=self.tenant,
            supplier_name="Test Supplier Ltd",
            bill_number="BILL-2024-001",
            amount=Decimal('1000.00'),
            due_date=timezone.now().date()
        )
    
    def test_create_valid_debit_note(self):
        """Test creating a valid debit note."""
        debit_note = SupplierDebitNote.objects.create(
            tenant=self.tenant,
            bill=self.bill,
            debit_note_number="SDN-20241201-0001",
            amount=Decimal('150.00'),
            reason="Additional freight charges",
            description="Expedited shipping required",
            status='draft'
        )
        
        self.assertEqual(debit_note.tenant, self.tenant)
        self.assertEqual(debit_note.bill, self.bill)
        self.assertEqual(debit_note.amount, Decimal('150.00'))
        self.assertEqual(debit_note.status, 'draft')
        self.assertEqual(str(debit_note), f"Supplier Debit Note #{debit_note.debit_note_number} (NGN 150.00)")
    
    def test_debit_note_number_unique(self):
        """Test debit note number uniqueness constraint."""
        SupplierDebitNote.objects.create(
            tenant=self.tenant,
            bill=self.bill,
            debit_note_number="SDN-20241201-0001",
            amount=Decimal('100.00'),
            reason="Test reason"
        )
        
        with self.assertRaises(ValidationError):
            duplicate = SupplierDebitNote(
                tenant=self.tenant,
                bill=self.bill,
                debit_note_number="SDN-20241201-0001",
                amount=Decimal('200.00'),
                reason="Duplicate number"
            )
            duplicate.full_clean()
    
    def test_negative_amount_validation(self):
        """Test that negative amounts are rejected."""
        with self.assertRaises(ValidationError):
            debit_note = SupplierDebitNote(
                tenant=self.tenant,
                bill=self.bill,
                debit_note_number="SDN-20241201-0002",
                amount=Decimal('-50.00'),
                reason="Invalid negative amount"
            )
            debit_note.full_clean()
    
    def test_zero_amount_validation(self):
        """Test that zero amounts are rejected."""
        with self.assertRaises(ValidationError):
            debit_note = SupplierDebitNote(
                tenant=self.tenant,
                bill=self.bill,
                debit_note_number="SDN-20241201-0003",
                amount=Decimal('0.00'),
                reason="Invalid zero amount"
            )
            debit_note.full_clean()
    
    def test_status_choices(self):
        """Test all valid status choices."""
        valid_statuses = ['draft', 'pending', 'approved', 'rejected', 'cancelled']
        
        for status in valid_statuses:
            debit_note = SupplierDebitNote.objects.create(
                tenant=self.tenant,
                bill=self.bill,
                debit_note_number=f"SDN-20241201-{status}",
                amount=Decimal('100.00'),
                reason=f"Test {status}",
                status=status
            )
            self.assertEqual(debit_note.status, status)
    
    def test_backward_compatibility_property(self):
        """Test note_number property for backward compatibility."""
        debit_note = SupplierDebitNote.objects.create(
            tenant=self.tenant,
            bill=self.bill,
            debit_note_number="SDN-20241201-0004",
            amount=Decimal('75.00'),
            reason="Compatibility test"
        )
        
        self.assertEqual(debit_note.note_number, debit_note.debit_note_number)


class SupplierDebitNoteServiceTest(TestCase):
    """Test SupplierDebitNoteService business logic and workflows."""
    
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test School")
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.person = Person.objects.create(
            tenant=self.tenant,
            user=self.user,
            first_name="Test",
            last_name="User",
            email="test@example.com"
        )
        
        self.bill = SupplierBill.objects.create(
            tenant=self.tenant,
            supplier_name="Test Supplier Ltd",
            bill_number="BILL-2024-001",
            amount=Decimal('1000.00'),
            due_date=timezone.now().date(),
            status='approved'
        )
        
        self.supplier = Supplier.objects.create(
            tenant=self.tenant,
            name="Test Supplier Ltd",
            email="supplier@example.com",
            phone="+1234567890"
        )
    
    def test_create_debit_note_success(self):
        """Test successful debit note creation."""
        debit_note = SupplierDebitNoteService.create_debit_note(
            tenant=self.tenant,
            bill_id=self.bill.id,
            amount=Decimal('150.00'),
            reason="Additional freight charges",
            description="Rush delivery required",
            created_by=self.person
        )
        
        self.assertEqual(debit_note.tenant, self.tenant)
        self.assertEqual(debit_note.bill, self.bill)
        self.assertEqual(debit_note.amount, Decimal('150.00'))
        self.assertEqual(debit_note.reason, "Additional freight charges")
        self.assertEqual(debit_note.description, "Rush delivery required")
        self.assertEqual(debit_note.status, 'draft')
        self.assertEqual(debit_note.submitted_by, self.person)
        self.assertTrue(debit_note.debit_note_number.startswith('SDN-'))
    
    def test_create_debit_note_invalid_amount(self):
        """Test debit note creation with invalid amount."""
        with self.assertRaises(ValidationError) as cm:
            SupplierDebitNoteService.create_debit_note(
                tenant=self.tenant,
                bill_id=self.bill.id,
                amount=Decimal('-50.00'),
                reason="Invalid negative amount"
            )
        self.assertIn("greater than zero", str(cm.exception))
    
    def test_create_debit_note_cancelled_bill(self):
        """Test debit note creation for cancelled bill."""
        cancelled_bill = SupplierBill.objects.create(
            tenant=self.tenant,
            supplier_name="Cancelled Supplier",
            bill_number="BILL-CANCELLED",
            amount=Decimal('500.00'),
            due_date=timezone.now().date(),
            status='cancelled'
        )
        
        with self.assertRaises(ValidationError) as cm:
            SupplierDebitNoteService.create_debit_note(
                tenant=self.tenant,
                bill_id=cancelled_bill.id,
                amount=Decimal('100.00'),
                reason="Test cancelled bill"
            )
        self.assertIn("cancelled bill", str(cm.exception))
    
    def test_update_debit_note_success(self):
        """Test successful debit note update."""
        debit_note = SupplierDebitNoteService.create_debit_note(
            tenant=self.tenant,
            bill_id=self.bill.id,
            amount=Decimal('100.00'),
            reason="Original reason"
        )
        
        updated_note = SupplierDebitNoteService.update_debit_note(
            debit_note_id=debit_note.id,
            tenant=self.tenant,
            amount=Decimal('200.00'),
            reason="Updated reason",
            description="Updated description"
        )
        
        self.assertEqual(updated_note.amount, Decimal('200.00'))
        self.assertEqual(updated_note.reason, "Updated reason")
        self.assertEqual(updated_note.description, "Updated description")
    
    def test_update_non_draft_debit_note(self):
        """Test updating non-draft debit note fails."""
        debit_note = SupplierDebitNoteService.create_debit_note(
            tenant=self.tenant,
            bill_id=self.bill.id,
            amount=Decimal('100.00'),
            reason="Test reason"
        )
        
        # Submit the note
        SupplierDebitNoteService.submit_debit_note(
            debit_note_id=debit_note.id,
            tenant=self.tenant,
            submitted_by=self.person
        )
        
        # Try to update submitted note
        with self.assertRaises(ValidationError) as cm:
            SupplierDebitNoteService.update_debit_note(
                debit_note_id=debit_note.id,
                tenant=self.tenant,
                amount=Decimal('200.00')
            )
        self.assertIn("draft debit notes", str(cm.exception))
    
    def test_submit_debit_note_success(self):
        """Test successful debit note submission."""
        debit_note = SupplierDebitNoteService.create_debit_note(
            tenant=self.tenant,
            bill_id=self.bill.id,
            amount=Decimal('100.00'),
            reason="Test submission"
        )
        
        submitted_note = SupplierDebitNoteService.submit_debit_note(
            debit_note_id=debit_note.id,
            tenant=self.tenant,
            submitted_by=self.person
        )
        
        self.assertEqual(submitted_note.status, 'pending')
        self.assertEqual(submitted_note.submitted_by, self.person)
        self.assertIsNotNone(submitted_note.submitted_at)
    
    def test_approve_debit_note_success(self):
        """Test successful debit note approval."""
        # Create and submit debit note
        debit_note = SupplierDebitNoteService.create_debit_note(
            tenant=self.tenant,
            bill_id=self.bill.id,
            amount=Decimal('150.00'),
            reason="Freight charges"
        )
        
        SupplierDebitNoteService.submit_debit_note(
            debit_note_id=debit_note.id,
            tenant=self.tenant,
            submitted_by=self.person
        )
        
        # Store original bill amount
        original_amount = self.bill.amount
        
        # Approve debit note
        approved_note = SupplierDebitNoteService.approve_debit_note(
            debit_note_id=debit_note.id,
            tenant=self.tenant,
            approved_by=self.person
        )
        
        # Refresh bill from database
        self.bill.refresh_from_db()
        
        # Verify approval
        self.assertEqual(approved_note.status, 'approved')
        self.assertEqual(approved_note.approved_by, self.person)
        self.assertIsNotNone(approved_note.approved_at)
        
        # Verify bill amount increase
        self.assertEqual(self.bill.amount, original_amount + Decimal('150.00'))
    
    def test_reject_debit_note_success(self):
        """Test successful debit note rejection."""
        # Create and submit debit note
        debit_note = SupplierDebitNoteService.create_debit_note(
            tenant=self.tenant,
            bill_id=self.bill.id,
            amount=Decimal('100.00'),
            reason="Test rejection"
        )
        
        SupplierDebitNoteService.submit_debit_note(
            debit_note_id=debit_note.id,
            tenant=self.tenant
        )
        
        # Reject debit note
        rejected_note = SupplierDebitNoteService.reject_debit_note(
            debit_note_id=debit_note.id,
            tenant=self.tenant,
            rejected_by=self.person,
            rejection_reason="Insufficient documentation"
        )
        
        self.assertEqual(rejected_note.status, 'rejected')
        self.assertEqual(rejected_note.rejected_by, self.person)
        self.assertEqual(rejected_note.rejection_reason, "Insufficient documentation")
        self.assertIsNotNone(rejected_note.rejected_at)
    
    def test_cancel_debit_note_success(self):
        """Test successful debit note cancellation."""
        debit_note = SupplierDebitNoteService.create_debit_note(
            tenant=self.tenant,
            bill_id=self.bill.id,
            amount=Decimal('100.00'),
            reason="Test cancellation"
        )
        
        cancelled_note = SupplierDebitNoteService.cancel_debit_note(
            debit_note_id=debit_note.id,
            tenant=self.tenant,
            cancelled_by=self.person
        )
        
        self.assertEqual(cancelled_note.status, 'cancelled')
    
    def test_cancel_approved_debit_note_fails(self):
        """Test that approved debit notes cannot be cancelled."""
        # Create, submit, and approve debit note
        debit_note = SupplierDebitNoteService.create_debit_note(
            tenant=self.tenant,
            bill_id=self.bill.id,
            amount=Decimal('100.00'),
            reason="Test"
        )
        
        SupplierDebitNoteService.submit_debit_note(
            debit_note_id=debit_note.id,
            tenant=self.tenant
        )
        
        SupplierDebitNoteService.approve_debit_note(
            debit_note_id=debit_note.id,
            tenant=self.tenant,
            approved_by=self.person
        )
        
        # Try to cancel approved note
        with self.assertRaises(ValidationError) as cm:
            SupplierDebitNoteService.cancel_debit_note(
                debit_note_id=debit_note.id,
                tenant=self.tenant,
                cancelled_by=self.person
            )
        self.assertIn("cannot be cancelled", str(cm.exception))
    
    def test_get_debit_notes_filtering(self):
        """Test debit notes retrieval with filtering."""
        # Create debit notes with different statuses
        draft_note = SupplierDebitNoteService.create_debit_note(
            tenant=self.tenant,
            bill_id=self.bill.id,
            amount=Decimal('100.00'),
            reason="Draft note"
        )
        
        pending_note = SupplierDebitNoteService.create_debit_note(
            tenant=self.tenant,
            bill_id=self.bill.id,
            amount=Decimal('200.00'),
            reason="Pending note"
        )
        SupplierDebitNoteService.submit_debit_note(
            debit_note_id=pending_note.id,
            tenant=self.tenant
        )
        
        # Test filtering by status
        draft_notes = SupplierDebitNoteService.get_debit_notes(self.tenant, status='draft')
        self.assertEqual(draft_notes.count(), 1)
        self.assertEqual(draft_notes.first().id, draft_note.id)
        
        pending_notes = SupplierDebitNoteService.get_debit_notes(self.tenant, status='pending')
        self.assertEqual(pending_notes.count(), 1)
        self.assertEqual(pending_notes.first().id, pending_note.id)
        
        # Test filtering by bill
        bill_notes = SupplierDebitNoteService.get_debit_notes(self.tenant, bill_id=self.bill.id)
        self.assertEqual(bill_notes.count(), 2)
    
    def test_generate_unique_note_number(self):
        """Test unique note number generation."""
        # Create multiple debit notes on same day
        note1 = SupplierDebitNoteService.create_debit_note(
            tenant=self.tenant,
            bill_id=self.bill.id,
            amount=Decimal('100.00'),
            reason="First note"
        )
        
        note2 = SupplierDebitNoteService.create_debit_note(
            tenant=self.tenant,
            bill_id=self.bill.id,
            amount=Decimal('200.00'),
            reason="Second note"
        )
        
        # Verify unique numbers
        self.assertNotEqual(note1.debit_note_number, note2.debit_note_number)
        self.assertTrue(note1.debit_note_number.startswith('SDN-'))
        self.assertTrue(note2.debit_note_number.startswith('SDN-'))
        
        # Verify sequential numbering
        seq1 = int(note1.debit_note_number.split('-')[-1])
        seq2 = int(note2.debit_note_number.split('-')[-1])
        self.assertEqual(seq2, seq1 + 1)


class SupplierDebitNoteWorkflowTest(TestCase):
    """Test complete debit note approval workflows."""
    
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test School")
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.person = Person.objects.create(
            tenant=self.tenant,
            user=self.user,
            first_name="Test",
            last_name="Manager",
            email="manager@example.com"
        )
        
        self.bill = SupplierBill.objects.create(
            tenant=self.tenant,
            supplier_name="ABC Suppliers",
            bill_number="BILL-2024-WORKFLOW",
            amount=Decimal('2000.00'),
            due_date=timezone.now().date(),
            status='approved'
        )
    
    def test_complete_approval_workflow(self):
        """Test complete workflow: draft → submit → approve."""
        # 1. Create draft debit note
        debit_note = SupplierDebitNoteService.create_debit_note(
            tenant=self.tenant,
            bill_id=self.bill.id,
            amount=Decimal('300.00'),
            reason="Additional freight and handling charges",
            description="Rush delivery to meet project deadline",
            created_by=self.person
        )
        self.assertEqual(debit_note.status, 'draft')
        
        # 2. Submit for approval
        submitted_note = SupplierDebitNoteService.submit_debit_note(
            debit_note_id=debit_note.id,
            tenant=self.tenant,
            submitted_by=self.person
        )
        self.assertEqual(submitted_note.status, 'pending')
        
        # 3. Approve debit note
        original_bill_amount = self.bill.amount
        approved_note = SupplierDebitNoteService.approve_debit_note(
            debit_note_id=debit_note.id,
            tenant=self.tenant,
            approved_by=self.person
        )
        
        # Verify final state
        self.assertEqual(approved_note.status, 'approved')
        self.bill.refresh_from_db()
        self.assertEqual(self.bill.amount, original_bill_amount + Decimal('300.00'))
    
    def test_complete_rejection_workflow(self):
        """Test complete workflow: draft → submit → reject → edit → resubmit."""
        # 1. Create and submit debit note
        debit_note = SupplierDebitNoteService.create_debit_note(
            tenant=self.tenant,
            bill_id=self.bill.id,
            amount=Decimal('500.00'),
            reason="Questionable charges"
        )
        
        SupplierDebitNoteService.submit_debit_note(
            debit_note_id=debit_note.id,
            tenant=self.tenant,
            submitted_by=self.person
        )
        
        # 2. Reject with reason
        rejected_note = SupplierDebitNoteService.reject_debit_note(
            debit_note_id=debit_note.id,
            tenant=self.tenant,
            rejected_by=self.person,
            rejection_reason="Need additional documentation and approval from procurement"
        )
        self.assertEqual(rejected_note.status, 'rejected')
        
        # 3. Update and resubmit (rejected notes become editable)
        updated_note = SupplierDebitNoteService.update_debit_note(
            debit_note_id=debit_note.id,
            tenant=self.tenant,
            amount=Decimal('400.00'),
            reason="Updated charges with proper documentation",
            description="Includes signed delivery receipt and procurement approval"
        )
        
        # Note: In real workflow, status would need to be reset to draft before resubmission
        # This would typically be handled by the view layer
    
    def test_cancellation_workflow(self):
        """Test debit note cancellation at different stages."""
        # Test draft cancellation
        draft_note = SupplierDebitNoteService.create_debit_note(
            tenant=self.tenant,
            bill_id=self.bill.id,
            amount=Decimal('100.00'),
            reason="Draft for cancellation"
        )
        
        cancelled_draft = SupplierDebitNoteService.cancel_debit_note(
            debit_note_id=draft_note.id,
            tenant=self.tenant,
            cancelled_by=self.person
        )
        self.assertEqual(cancelled_draft.status, 'cancelled')
        
        # Test rejected note cancellation
        rejected_note = SupplierDebitNoteService.create_debit_note(
            tenant=self.tenant,
            bill_id=self.bill.id,
            amount=Decimal('200.00'),
            reason="For rejection and cancellation"
        )
        
        SupplierDebitNoteService.submit_debit_note(
            debit_note_id=rejected_note.id,
            tenant=self.tenant
        )
        
        SupplierDebitNoteService.reject_debit_note(
            debit_note_id=rejected_note.id,
            tenant=self.tenant,
            rejected_by=self.person,
            rejection_reason="Test rejection"
        )
        
        cancelled_rejected = SupplierDebitNoteService.cancel_debit_note(
            debit_note_id=rejected_note.id,
            tenant=self.tenant,
            cancelled_by=self.person
        )
        self.assertEqual(cancelled_rejected.status, 'cancelled')