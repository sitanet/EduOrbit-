import uuid
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError

from backend.apps.efbm.models import (
    SupplierBill, SupplierCreditNote, SupplierLedger, SupplierBalance, Supplier
)
from backend.apps.efbm.services.integration import AutomaticAccountingIntegrationService


class SupplierCreditNoteService:
    """
    Enterprise Supplier Credit Note Service for EduOrbit ERP.
    Implements complete credit note lifecycle: creation, submission, approval, rejection,
    cancellation, supplier ledger updates, and automatic GL journal postings.
    Follows IFRS/IAS & GAAP accounting standards and Nigerian business regulations.
    """

    @classmethod
    @transaction.atomic
    def create_credit_note(cls, tenant, bill_id, amount, reason, created_by=None):
        """
        Create a new supplier credit note in draft status.
        
        Args:
            tenant: Tenant instance
            bill_id: UUID of SupplierBill
            amount: Decimal amount of credit note
            reason: Text description of credit note reason
            created_by: Person instance who created the note
            
        Returns:
            SupplierCreditNote instance
            
        Raises:
            ValidationError: If validation fails
            SupplierBill.DoesNotExist: If bill not found
        """
        bill = SupplierBill.objects.select_for_update().get(id=bill_id, tenant=tenant)
        amount = Decimal(str(amount))
        
        # Validation
        if amount <= Decimal('0.00'):
            raise ValidationError('Credit note amount must be greater than zero.')
        
        if amount > bill.outstanding_amount:
            raise ValidationError(
                f'Credit note amount (NGN {amount}) cannot exceed '
                f'bill outstanding amount (NGN {bill.outstanding_amount}).'
            )
        
        if bill.status == 'cancelled':
            raise ValidationError('Cannot create credit note for cancelled bill.')
        
        # Generate unique note number
        note_number = cls._generate_note_number(tenant)
        
        # Create credit note
        credit_note = SupplierCreditNote.objects.create(
            tenant=tenant,
            bill=bill,
            note_number=note_number,
            amount=amount,
            reason=reason,
            status='draft',
            issue_date=timezone.now().date(),
            submitted_by=created_by
        )
        
        return credit_note
    
    @classmethod
    @transaction.atomic
    def update_credit_note(cls, credit_note_id, tenant, amount=None, reason=None, updated_by=None):
        """
        Update draft credit note.
        
        Args:
            credit_note_id: UUID of credit note
            tenant: Tenant instance
            amount: Optional new amount
            reason: Optional new reason
            updated_by: Person who updated
            
        Returns:
            Updated SupplierCreditNote instance
            
        Raises:
            ValidationError: If not in draft status or validation fails
        """
        credit_note = SupplierCreditNote.objects.select_for_update().get(
            id=credit_note_id,
            tenant=tenant
        )
        
        if credit_note.status != 'draft':
            raise ValidationError('Only draft credit notes can be updated.')
        
        if amount is not None:
            amount = Decimal(str(amount))
            if amount <= Decimal('0.00'):
                raise ValidationError('Credit note amount must be greater than zero.')
            
            if amount > credit_note.bill.outstanding_amount:
                raise ValidationError(
                    f'Credit note amount (NGN {amount}) cannot exceed '
                    f'bill outstanding amount (NGN {credit_note.bill.outstanding_amount}).'
                )
            credit_note.amount = amount
        
        if reason is not None:
            credit_note.reason = reason
        
        credit_note.save()
        return credit_note

    
    @classmethod
    @transaction.atomic
    def submit_credit_note(cls, credit_note_id, tenant, submitted_by=None):
        """
        Submit draft credit note for approval.
        
        Args:
            credit_note_id: UUID of credit note
            tenant: Tenant instance
            submitted_by: Person submitting the note
            
        Returns:
            Updated SupplierCreditNote instance
            
        Raises:
            ValidationError: If not in draft status
        """
        credit_note = SupplierCreditNote.objects.select_for_update().get(
            id=credit_note_id,
            tenant=tenant
        )
        
        if credit_note.status != 'draft':
            raise ValidationError('Only draft credit notes can be submitted.')
        
        credit_note.status = 'submitted'
        credit_note.submitted_by = submitted_by
        credit_note.submitted_at = timezone.now()
        credit_note.save()
        
        return credit_note
    
    @classmethod
    @transaction.atomic
    def approve_credit_note(cls, credit_note_id, tenant, approved_by):
        """
        Approve submitted credit note and post accounting entries.
        
        This method performs:
        1. Status update to approved
        2. Reduces supplier bill outstanding amount
        3. Updates supplier ledger (credit entry)
        4. Updates supplier balance
        5. Posts balanced journal entry (DR: Accounts Payable, CR: Administrative Expenses)
        
        Args:
            credit_note_id: UUID of credit note
            tenant: Tenant instance
            approved_by: Person instance approving the note (required)
            
        Returns:
            Approved SupplierCreditNote instance
            
        Raises:
            ValidationError: If not in submitted status or validation fails
        """
        if not approved_by:
            raise ValidationError('Approver is required.')
        
        credit_note = SupplierCreditNote.objects.select_for_update().get(
            id=credit_note_id,
            tenant=tenant
        )
        
        if credit_note.status != 'submitted':
            raise ValidationError('Only submitted credit notes can be approved.')
        
        bill = SupplierBill.objects.select_for_update().get(id=credit_note.bill.id)
        
        # Validate amount doesn't exceed bill outstanding
        if credit_note.amount > bill.outstanding_amount:
            raise ValidationError(
                f'Credit note amount (NGN {credit_note.amount}) exceeds '
                f'bill outstanding amount (NGN {bill.outstanding_amount}).'
            )
        
        # Update credit note status
        credit_note.status = 'approved'
        credit_note.approved_by = approved_by
        credit_note.approved_at = timezone.now()
        credit_note.save()
        
        # Reduce bill outstanding amount (credit reduces payable)
        bill.paid_amount += credit_note.amount
        if bill.paid_amount >= bill.amount:
            bill.status = 'paid'
        elif bill.paid_amount > Decimal('0.00'):
            bill.status = 'partial'
        bill.save()
        
        # Update supplier ledger (credit entry)
        cls._update_supplier_ledger(
            tenant=tenant,
            bill=bill,
            credit_note=credit_note,
            amount=credit_note.amount,
            transaction_type='credit'
        )
        
        # Update supplier balance
        cls._update_supplier_balance(tenant, bill.supplier_name, credit_note.amount, 'credit')
        
        # Post journal entry (DR: Accounts Payable, CR: Administrative Expenses)
        AutomaticAccountingIntegrationService.post_supplier_credit_note(
            tenant=tenant,
            reference_id=str(credit_note.id),
            amount=credit_note.amount
        )
        
        return credit_note

    
    @classmethod
    @transaction.atomic
    def reject_credit_note(cls, credit_note_id, tenant, rejected_by, rejection_reason):
        """
        Reject submitted credit note and return to draft.
        
        Args:
            credit_note_id: UUID of credit note
            tenant: Tenant instance
            rejected_by: Person rejecting the note
            rejection_reason: Text reason for rejection (required)
            
        Returns:
            Rejected SupplierCreditNote instance
            
        Raises:
            ValidationError: If not in submitted status or no reason provided
        """
        if not rejection_reason or not rejection_reason.strip():
            raise ValidationError('Rejection reason is required.')
        
        credit_note = SupplierCreditNote.objects.select_for_update().get(
            id=credit_note_id,
            tenant=tenant
        )
        
        if credit_note.status != 'submitted':
            raise ValidationError('Only submitted credit notes can be rejected.')
        
        credit_note.status = 'rejected'
        credit_note.rejection_reason = rejection_reason
        credit_note.save()
        
        return credit_note
    
    @classmethod
    @transaction.atomic
    def cancel_credit_note(cls, credit_note_id, tenant, cancelled_by):
        """
        Cancel draft or rejected credit note.
        Approved credit notes cannot be cancelled (use reversal journal instead).
        
        Args:
            credit_note_id: UUID of credit note
            tenant: Tenant instance
            cancelled_by: Person cancelling the note
            
        Returns:
            Cancelled SupplierCreditNote instance
            
        Raises:
            ValidationError: If already approved or cancelled
        """
        credit_note = SupplierCreditNote.objects.select_for_update().get(
            id=credit_note_id,
            tenant=tenant
        )
        
        if credit_note.status == 'approved':
            raise ValidationError(
                'Approved credit notes cannot be cancelled. Use journal reversal instead.'
            )
        
        if credit_note.status == 'cancelled':
            raise ValidationError('Credit note is already cancelled.')
        
        credit_note.status = 'cancelled'
        credit_note.save()
        
        return credit_note
    
    @classmethod
    def get_credit_notes(cls, tenant, status=None, bill_id=None):
        """
        Retrieve credit notes with optional filtering.
        
        Args:
            tenant: Tenant instance
            status: Optional status filter
            bill_id: Optional bill ID filter
            
        Returns:
            QuerySet of SupplierCreditNote
        """
        queryset = SupplierCreditNote.objects.filter(tenant=tenant).select_related(
            'bill',
            'submitted_by',
            'approved_by'
        )
        
        if status:
            queryset = queryset.filter(status=status)
        
        if bill_id:
            queryset = queryset.filter(bill_id=bill_id)
        
        return queryset.order_by('-issue_date', '-created_at')
    
    @classmethod
    def get_credit_note(cls, credit_note_id, tenant):
        """
        Retrieve single credit note with related data.
        
        Args:
            credit_note_id: UUID of credit note
            tenant: Tenant instance
            
        Returns:
            SupplierCreditNote instance
        """
        return SupplierCreditNote.objects.select_related(
            'bill',
            'submitted_by',
            'approved_by'
        ).get(id=credit_note_id, tenant=tenant)

    
    @classmethod
    def _generate_note_number(cls, tenant):
        """
        Generate unique credit note number.
        Format: SCN-YYYYMMDD-XXXX
        
        Args:
            tenant: Tenant instance
            
        Returns:
            Unique note number string
        """
        today = timezone.now().date()
        date_prefix = today.strftime('%Y%m%d')
        
        last_note = SupplierCreditNote.objects.filter(
            tenant=tenant,
            note_number__startswith=f'SCN-{date_prefix}'
        ).order_by('-note_number').first()
        
        if last_note:
            try:
                last_seq = int(last_note.note_number.split('-')[-1])
                new_seq = last_seq + 1
            except (IndexError, ValueError):
                new_seq = 1
        else:
            new_seq = 1
        
        return f'SCN-{date_prefix}-{new_seq:04d}'
    
    @classmethod
    def _update_supplier_ledger(cls, tenant, bill, credit_note, amount, transaction_type):
        """
        Create supplier ledger entry for credit note.
        
        Args:
            tenant: Tenant instance
            bill: SupplierBill instance
            credit_note: SupplierCreditNote instance
            amount: Decimal amount
            transaction_type: 'credit' for credit notes
        """
        # Get supplier from bill
        supplier = Supplier.objects.filter(
            tenant=tenant,
            name=bill.supplier_name
        ).first()
        
        if not supplier:
            return
        
        # Get current balance
        last_ledger = SupplierLedger.objects.filter(
            tenant=tenant,
            supplier=supplier
        ).order_by('-transaction_date', '-created_at').first()
        
        current_balance = last_ledger.balance_after if last_ledger else Decimal('0.00')
        
        # Credit reduces payable (subtract from balance)
        new_balance = current_balance - amount
        
        # Create ledger entry
        SupplierLedger.objects.create(
            tenant=tenant,
            supplier=supplier,
            transaction_date=credit_note.issue_date,
            description=f'Credit Note {credit_note.note_number} - {credit_note.reason[:100]}',
            reference_number=credit_note.note_number,
            debit_amount=Decimal('0.00'),
            credit_amount=amount,
            balance_after=new_balance,
            bill=bill
        )
    
    @classmethod
    def _update_supplier_balance(cls, tenant, supplier_name, amount, transaction_type):
        """
        Update or create supplier balance record.
        
        Args:
            tenant: Tenant instance
            supplier_name: Name of supplier
            amount: Decimal amount
            transaction_type: 'credit' for credit notes
        """
        supplier = Supplier.objects.filter(
            tenant=tenant,
            name=supplier_name
        ).first()
        
        if not supplier:
            return
        
        balance, created = SupplierBalance.objects.get_or_create(
            tenant=tenant,
            supplier=supplier,
            defaults={
                'current_balance': Decimal('0.00'),
                'total_billed': Decimal('0.00'),
                'total_paid': Decimal('0.00')
            }
        )
        
        # Credit reduces payable
        balance.current_balance -= amount
        balance.last_transaction_date = timezone.now().date()
        balance.save()
