import uuid
from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone

from backend.apps.tenants.models import Tenant
from backend.apps.people.models import Person
from backend.apps.efbm.models import (
    SupplierBill, SupplierCreditNote, Supplier, SupplierLedger, SupplierBalance
)
from backend.apps.efbm.services.supplier_credit_notes import SupplierCreditNoteService


class SupplierCreditNoteServiceTest(TestCase):
    """
    Test suite for SupplierCreditNoteService covering complete enterprise functionality.
    """

    def setUp(self):
        """Set up test data for each test method."""
        self.tenant = Tenant.objects.create(name='Test School')
        
        # Create supplier
        self.supplier = Supplier.objects.create(
            tenant=self.tenant,
            name='Test Supplier Ltd',
            email='supplier@test.com',
            phone='+234123456789'
        )
        
        # Create supplier bill
        self.bill = SupplierBill.objects.create(
            tenant=self.tenant,
            supplier_name=self.supplier.name,
            bill_number='INV-2026-001',
            issue_date=timezone.now().date(),
            due_date=timezone.now().date(),
            amount=Decimal('100000.00'),
            paid_amount=Decimal('0.00'),
            status='approved',
            category='General Supplies'
        )
        
        # Create person for approvals
        self.person = Person.objects.create(
            tenant=self.tenant,
            person_number='PER-001',
            first_name='John',
            last_name='Approver',
            date_of_birth=timezone.now().date(),
            gender='male'
        )

    def test_create_credit_note_success(self):
        """Test successful credit note creation."""
        credit_note = SupplierCreditNoteService.create_credit_note(
            tenant=self.tenant,
            bill_id=self.bill.id,
            amount=Decimal('10000.00'),
            reason='Damaged goods return',
            created_by=self.person
        )
        
        self.assertIsInstance(credit_note, SupplierCreditNote)
        self.assertEqual(credit_note.tenant, self.tenant)
        self.assertEqual(credit_note.bill, self.bill)
        self.assertEqual(credit_note.amount, Decimal('10000.00'))
        self.assertEqual(credit_note.reason, 'Damaged goods return')
        self.assertEqual(credit_note.status, 'draft')
        self.assertEqual(credit_note.submitted_by, self.person)
        self.assertTrue(credit_note.note_number.startswith('SCN-'))

    def test_create_credit_note_amount_exceeds_outstanding(self):
        """Test credit note creation fails when amount exceeds outstanding."""
        with self.assertRaises(ValidationError) as context:
            SupplierCreditNoteService.create_credit_note(
                tenant=self.tenant,
                bill_id=self.bill.id,
                amount=Decimal('150000.00'),  # Exceeds bill amount
                reason='Invalid amount test',
                created_by=self.person
            )
        
        self.assertIn('cannot exceed', str(context.exception))

    def test_create_credit_note_zero_amount(self):
        """Test credit note creation fails with zero amount."""
        with self.assertRaises(ValidationError) as context:
            SupplierCreditNoteService.create_credit_note(
                tenant=self.tenant,
                bill_id=self.bill.id,
                amount=Decimal('0.00'),
                reason='Zero amount test',
                created_by=self.person
            )
        
        self.assertIn('must be greater than zero', str(context.exception))

    def test_create_credit_note_cancelled_bill(self):
        """Test credit note creation fails for cancelled bill."""
        self.bill.status = 'cancelled'
        self.bill.save()
        
        with self.assertRaises(ValidationError) as context:
            SupplierCreditNoteService.create_credit_note(
                tenant=self.tenant,
                bill_id=self.bill.id,
                amount=Decimal('10000.00'),
                reason='Cancelled bill test',
                created_by=self.person
            )
        
        self.assertIn('cancelled bill', str(context.exception))

    def test_update_credit_note_success(self):
        """Test successful credit note update."""
        credit_note = SupplierCreditNoteService.create_credit_note(
            tenant=self.tenant,
            bill_id=self.bill.id,
            amount=Decimal('10000.00'),
            reason='Original reason',
            created_by=self.person
        )
        
        updated_note = SupplierCreditNoteService.update_credit_note(
            credit_note_id=credit_note.id,
            tenant=self.tenant,
            amount=Decimal('15000.00'),
            reason='Updated reason',
            updated_by=self.person
        )
        
        self.assertEqual(updated_note.amount, Decimal('15000.00'))
        self.assertEqual(updated_note.reason, 'Updated reason')

    def test_update_credit_note_non_draft_status(self):
        """Test credit note update fails for non-draft status."""
        credit_note = SupplierCreditNoteService.create_credit_note(
            tenant=self.tenant,
            bill_id=self.bill.id,
            amount=Decimal('10000.00'),
            reason='Test reason',
            created_by=self.person
        )
        
        # Submit the credit note
        credit_note.status = 'submitted'
        credit_note.save()
        
        with self.assertRaises(ValidationError) as context:
            SupplierCreditNoteService.update_credit_note(
                credit_note_id=credit_note.id,
                tenant=self.tenant,
                amount=Decimal('15000.00'),
                updated_by=self.person
            )
        
        self.assertIn('Only draft credit notes can be updated', str(context.exception))

    def test_submit_credit_note_success(self):
        """Test successful credit note submission."""
        credit_note = SupplierCreditNoteService.create_credit_note(
            tenant=self.tenant,
            bill_id=self.bill.id,
            amount=Decimal('10000.00'),
            reason='Test submission',
            created_by=self.person
        )
        
        submitted_note = SupplierCreditNoteService.submit_credit_note(
            credit_note_id=credit_note.id,
            tenant=self.tenant,
            submitted_by=self.person
        )
        
        self.assertEqual(submitted_note.status, 'submitted')
        self.assertEqual(submitted_note.submitted_by, self.person)
        self.assertIsNotNone(submitted_note.submitted_at)

    def test_submit_credit_note_non_draft_status(self):
        """Test credit note submission fails for non-draft status."""
        credit_note = SupplierCreditNoteService.create_credit_note(
            tenant=self.tenant,
            bill_id=self.bill.id,
            amount=Decimal('10000.00'),
            reason='Test reason',
            created_by=self.person
        )
        
        credit_note.status = 'approved'
        credit_note.save()
        
        with self.assertRaises(ValidationError) as context:
            SupplierCreditNoteService.submit_credit_note(
                credit_note_id=credit_note.id,
                tenant=self.tenant,
                submitted_by=self.person
            )
        
        self.assertIn('Only draft credit notes can be submitted', str(context.exception))

    def test_approve_credit_note_success(self):
        """Test successful credit note approval and accounting integration."""
        credit_note = SupplierCreditNoteService.create_credit_note(
            tenant=self.tenant,
            bill_id=self.bill.id,
            amount=Decimal('10000.00'),
            reason='Test approval',
            created_by=self.person
        )
        
        # Submit first
        credit_note.status = 'submitted'
        credit_note.save()
        
        # Approve
        approved_note = SupplierCreditNoteService.approve_credit_note(
            credit_note_id=credit_note.id,
            tenant=self.tenant,
            approved_by=self.person
        )
        
        # Verify credit note status
        self.assertEqual(approved_note.status, 'approved')
        self.assertEqual(approved_note.approved_by, self.person)
        self.assertIsNotNone(approved_note.approved_at)
        
        # Verify bill paid amount updated
        self.bill.refresh_from_db()
        self.assertEqual(self.bill.paid_amount, Decimal('10000.00'))
        self.assertEqual(self.bill.status, 'partial')
        
        # Verify supplier ledger entry created
        ledger_entries = SupplierLedger.objects.filter(
            tenant=self.tenant,
            supplier=self.supplier
        )
        self.assertTrue(ledger_entries.exists())
        
        ledger_entry = ledger_entries.first()
        self.assertEqual(ledger_entry.credit_amount, Decimal('10000.00'))
        self.assertEqual(ledger_entry.debit_amount, Decimal('0.00'))
        self.assertEqual(ledger_entry.bill, self.bill)

    def test_approve_credit_note_no_approver(self):
        """Test credit note approval fails without approver."""
        credit_note = SupplierCreditNoteService.create_credit_note(
            tenant=self.tenant,
            bill_id=self.bill.id,
            amount=Decimal('10000.00'),
            reason='Test approval',
            created_by=self.person
        )
        
        credit_note.status = 'submitted'
        credit_note.save()
        
        with self.assertRaises(ValidationError) as context:
            SupplierCreditNoteService.approve_credit_note(
                credit_note_id=credit_note.id,
                tenant=self.tenant,
                approved_by=None
            )
        
        self.assertIn('Approver is required', str(context.exception))

    def test_approve_credit_note_non_submitted_status(self):
        """Test credit note approval fails for non-submitted status."""
        credit_note = SupplierCreditNoteService.create_credit_note(
            tenant=self.tenant,
            bill_id=self.bill.id,
            amount=Decimal('10000.00'),
            reason='Test approval',
            created_by=self.person
        )
        
        with self.assertRaises(ValidationError) as context:
            SupplierCreditNoteService.approve_credit_note(
                credit_note_id=credit_note.id,
                tenant=self.tenant,
                approved_by=self.person
            )
        
        self.assertIn('Only submitted credit notes can be approved', str(context.exception))

    def test_reject_credit_note_success(self):
        """Test successful credit note rejection."""
        credit_note = SupplierCreditNoteService.create_credit_note(
            tenant=self.tenant,
            bill_id=self.bill.id,
            amount=Decimal('10000.00'),
            reason='Test rejection',
            created_by=self.person
        )
        
        credit_note.status = 'submitted'
        credit_note.save()
        
        rejected_note = SupplierCreditNoteService.reject_credit_note(
            credit_note_id=credit_note.id,
            tenant=self.tenant,
            rejected_by=self.person,
            rejection_reason='Insufficient documentation'
        )
        
        self.assertEqual(rejected_note.status, 'rejected')
        self.assertEqual(rejected_note.rejection_reason, 'Insufficient documentation')

    def test_reject_credit_note_no_reason(self):
        """Test credit note rejection fails without reason."""
        credit_note = SupplierCreditNoteService.create_credit_note(
            tenant=self.tenant,
            bill_id=self.bill.id,
            amount=Decimal('10000.00'),
            reason='Test rejection',
            created_by=self.person
        )
        
        credit_note.status = 'submitted'
        credit_note.save()
        
        with self.assertRaises(ValidationError) as context:
            SupplierCreditNoteService.reject_credit_note(
                credit_note_id=credit_note.id,
                tenant=self.tenant,
                rejected_by=self.person,
                rejection_reason=''
            )
        
        self.assertIn('Rejection reason is required', str(context.exception))

    def test_cancel_credit_note_success(self):
        """Test successful credit note cancellation."""
        credit_note = SupplierCreditNoteService.create_credit_note(
            tenant=self.tenant,
            bill_id=self.bill.id,
            amount=Decimal('10000.00'),
            reason='Test cancellation',
            created_by=self.person
        )
        
        cancelled_note = SupplierCreditNoteService.cancel_credit_note(
            credit_note_id=credit_note.id,
            tenant=self.tenant,
            cancelled_by=self.person
        )
        
        self.assertEqual(cancelled_note.status, 'cancelled')

    def test_cancel_approved_credit_note_fails(self):
        """Test cancellation fails for approved credit note."""
        credit_note = SupplierCreditNoteService.create_credit_note(
            tenant=self.tenant,
            bill_id=self.bill.id,
            amount=Decimal('10000.00'),
            reason='Test cancellation',
            created_by=self.person
        )
        
        credit_note.status = 'approved'
        credit_note.save()
        
        with self.assertRaises(ValidationError) as context:
            SupplierCreditNoteService.cancel_credit_note(
                credit_note_id=credit_note.id,
                tenant=self.tenant,
                cancelled_by=self.person
            )
        
        self.assertIn('Approved credit notes cannot be cancelled', str(context.exception))

    def test_get_credit_notes_filtering(self):
        """Test credit note retrieval with filtering."""
        # Create multiple credit notes
        cn1 = SupplierCreditNoteService.create_credit_note(
            tenant=self.tenant,
            bill_id=self.bill.id,
            amount=Decimal('5000.00'),
            reason='First note',
            created_by=self.person
        )
        
        cn2 = SupplierCreditNoteService.create_credit_note(
            tenant=self.tenant,
            bill_id=self.bill.id,
            amount=Decimal('3000.00'),
            reason='Second note',
            created_by=self.person
        )
        
        cn2.status = 'submitted'
        cn2.save()
        
        # Test filtering by status
        draft_notes = SupplierCreditNoteService.get_credit_notes(
            tenant=self.tenant,
            status='draft'
        )
        self.assertEqual(draft_notes.count(), 1)
        self.assertEqual(draft_notes.first().id, cn1.id)
        
        submitted_notes = SupplierCreditNoteService.get_credit_notes(
            tenant=self.tenant,
            status='submitted'
        )
        self.assertEqual(submitted_notes.count(), 1)
        self.assertEqual(submitted_notes.first().id, cn2.id)
        
        # Test filtering by bill
        bill_notes = SupplierCreditNoteService.get_credit_notes(
            tenant=self.tenant,
            bill_id=self.bill.id
        )
        self.assertEqual(bill_notes.count(), 2)

    def test_generate_note_number_uniqueness(self):
        """Test credit note number generation ensures uniqueness."""
        # Create multiple credit notes on same day
        cn1 = SupplierCreditNoteService.create_credit_note(
            tenant=self.tenant,
            bill_id=self.bill.id,
            amount=Decimal('1000.00'),
            reason='First note',
            created_by=self.person
        )
        
        cn2 = SupplierCreditNoteService.create_credit_note(
            tenant=self.tenant,
            bill_id=self.bill.id,
            amount=Decimal('2000.00'),
            reason='Second note',
            created_by=self.person
        )
        
        # Verify different note numbers
        self.assertNotEqual(cn1.note_number, cn2.note_number)
        self.assertTrue(cn1.note_number.startswith('SCN-'))
        self.assertTrue(cn2.note_number.startswith('SCN-'))
        
        # Verify sequential numbering
        cn1_seq = int(cn1.note_number.split('-')[-1])
        cn2_seq = int(cn2.note_number.split('-')[-1])
        self.assertEqual(cn2_seq, cn1_seq + 1)

    def test_supplier_balance_update_on_approval(self):
        """Test supplier balance is correctly updated on credit note approval."""
        # Create initial balance
        SupplierBalance.objects.create(
            tenant=self.tenant,
            supplier=self.supplier,
            current_balance=Decimal('50000.00'),
            total_billed=Decimal('100000.00'),
            total_paid=Decimal('50000.00')
        )
        
        credit_note = SupplierCreditNoteService.create_credit_note(
            tenant=self.tenant,
            bill_id=self.bill.id,
            amount=Decimal('10000.00'),
            reason='Test balance update',
            created_by=self.person
        )
        
        credit_note.status = 'submitted'
        credit_note.save()
        
        # Approve credit note
        SupplierCreditNoteService.approve_credit_note(
            credit_note_id=credit_note.id,
            tenant=self.tenant,
            approved_by=self.person
        )
        
        # Verify balance updated
        balance = SupplierBalance.objects.get(tenant=self.tenant, supplier=self.supplier)
        self.assertEqual(balance.current_balance, Decimal('40000.00'))  # 50000 - 10000

    def test_full_workflow_integration(self):
        """Test complete credit note workflow from creation to approval."""
        # Create credit note
        credit_note = SupplierCreditNoteService.create_credit_note(
            tenant=self.tenant,
            bill_id=self.bill.id,
            amount=Decimal('25000.00'),
            reason='Complete workflow test - overcharge correction',
            created_by=self.person
        )
        
        # Verify initial state
        self.assertEqual(credit_note.status, 'draft')
        self.assertIsNone(credit_note.submitted_at)
        self.assertIsNone(credit_note.approved_at)
        
        # Submit for approval
        credit_note = SupplierCreditNoteService.submit_credit_note(
            credit_note_id=credit_note.id,
            tenant=self.tenant,
            submitted_by=self.person
        )
        
        # Verify submitted state
        self.assertEqual(credit_note.status, 'submitted')
        self.assertIsNotNone(credit_note.submitted_at)
        self.assertEqual(credit_note.submitted_by, self.person)
        
        # Approve credit note
        credit_note = SupplierCreditNoteService.approve_credit_note(
            credit_note_id=credit_note.id,
            tenant=self.tenant,
            approved_by=self.person
        )
        
        # Verify approved state and effects
        self.assertEqual(credit_note.status, 'approved')
        self.assertIsNotNone(credit_note.approved_at)
        self.assertEqual(credit_note.approved_by, self.person)
        
        # Verify bill updated
        self.bill.refresh_from_db()
        self.assertEqual(self.bill.paid_amount, Decimal('25000.00'))
        self.assertEqual(self.bill.status, 'partial')
        
        # Verify ledger entry
        ledger_entry = SupplierLedger.objects.get(
            tenant=self.tenant,
            supplier=self.supplier,
            reference_number=credit_note.note_number
        )
        self.assertEqual(ledger_entry.credit_amount, Decimal('25000.00'))
        self.assertIn('overcharge correction', ledger_entry.description.lower())