from decimal import Decimal
import uuid
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import Sum
from backend.apps.efbm.models import (
    SupplierBill, SupplierPayment, SupplierCreditNote, SupplierDebitNote, 
    SupplierBalance, SupplierLedger, Supplier, PaymentVoucher, BankAccount
)
from backend.apps.efbm.services.integration import AutomaticAccountingIntegrationService


class AccountsPayableService:
    """
    Enterprise Accounts Payable (AP) Service.
    """
    @classmethod
    def get_payables_dashboard_widgets(cls, tenant):
        bills = SupplierBill.objects.all()
        if tenant:
            bills = bills.filter(tenant=tenant)

        total_billed = sum(b.amount for b in bills)
        total_paid = sum(b.paid_amount for b in bills)
        total_payables = total_billed - total_paid

        return {
            'total_billed': total_billed,
            'total_paid': total_paid,
            'total_payables': total_payables,
            'pending_count': bills.filter(status='pending').count()
        }

    @classmethod
    def get_vendor_aging(cls, tenant):
        bills = SupplierBill.objects.filter(status__in=['pending', 'approved', 'partial'])
        if tenant:
            bills = bills.filter(tenant=tenant)

        return {
            '0_30': sum(b.outstanding_amount for b in bills),
            '31_60': Decimal('0.00'),
            '61_90': Decimal('0.00'),
            '90_plus': Decimal('0.00')
        }

    @classmethod
    def get_supplier_bills(cls, tenant, status=None):
        """
        Retrieve supplier bills with optional status filtering.
        
        Args:
            tenant: Tenant instance
            status: Optional status filter
            
        Returns:
            QuerySet of SupplierBill
        """
        queryset = SupplierBill.objects.filter(tenant=tenant).order_by('-issue_date', '-created_at')
        
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset

    @classmethod
    @transaction.atomic
    def create_credit_note(cls, tenant, bill_id, amount, reason):
        """
        Creates a Supplier Credit Note reducing vendor liability, updating SupplierBalance,
        posting to SupplierLedger, and generating double-entry GL journal postings.
        """
        amt = Decimal(str(amount))
        bill = SupplierBill.objects.get(id=bill_id)

        note_num = f"CN-SUP-{str(uuid.uuid4())[:8].upper()}"
        cn = SupplierCreditNote.objects.create(
            tenant=tenant,
            bill=bill,
            note_number=note_num,
            amount=amt,
            reason=reason,
            issue_date=timezone.now()
        )

        # Reduce bill paid/outstanding status
        bill.paid_amount += amt
        if bill.paid_amount >= bill.amount:
            bill.status = 'paid'
        elif bill.paid_amount > Decimal('0.00'):
            bill.status = 'partial'
        bill.save()

        # Update SupplierBalance control account if bill is associated with a supplier
        if hasattr(bill, 'supplier') and bill.supplier:
            bal, _ = SupplierBalance.objects.get_or_create(tenant=tenant, supplier=bill.supplier)
            bal.total_credit_notes += amt
            bal.current_balance = bal.total_bills + bal.total_debit_notes - bal.total_credit_notes - bal.total_payments
            bal.last_transaction_date = timezone.now().date()
            bal.last_recalculated_at = timezone.now()
            bal.save()

            # Log into SupplierLedger
            SupplierLedger.objects.create(
                tenant=tenant,
                supplier=bill.supplier,
                transaction_date=timezone.now().date(),
                description=f"Supplier Credit Note #{note_num} - {reason}",
                reference_number=note_num,
                credit_amount=amt,
                balance_after=bal.current_balance,
                bill=bill
            )

        # Automatic GL Journal Entry
        AutomaticAccountingIntegrationService.post_supplier_credit_note(
            tenant=tenant,
            reference_id=cn.note_number,
            amount=amt
        )

        return cn

    @classmethod
    def get_supplier_credit_notes(cls, tenant):
        cns = SupplierCreditNote.objects.select_related('bill').all()
        if tenant:
            cns = cns.filter(tenant=tenant)
        return cns.order_by('-issue_date')


class SupplierDebitNoteService:
    """
    Enterprise Supplier Debit Note Service for EduOrbit ERP.
    Implements complete debit note lifecycle: creation, submission, approval, rejection,
    cancellation, supplier ledger updates, and automatic GL journal postings.
    Follows IFRS/IAS & GAAP accounting standards and Nigerian business regulations.
    """

    @classmethod
    @transaction.atomic
    def create_debit_note(cls, tenant, bill_id, amount, reason, description=None, created_by=None):
        """
        Create a new supplier debit note in draft status.
        
        Args:
            tenant: Tenant instance
            bill_id: UUID of SupplierBill
            amount: Decimal amount of debit note
            reason: Text description of debit note reason
            description: Optional detailed description
            created_by: Person instance who created the note
            
        Returns:
            SupplierDebitNote instance
            
        Raises:
            ValidationError: If validation fails
            SupplierBill.DoesNotExist: If bill not found
        """
        bill = SupplierBill.objects.select_for_update().get(id=bill_id, tenant=tenant)
        amount = Decimal(str(amount))
        
        # Validation
        if amount <= Decimal('0.00'):
            raise ValidationError('Debit note amount must be greater than zero.')
        
        if bill.status == 'cancelled':
            raise ValidationError('Cannot create debit note for cancelled bill.')
        
        # Generate unique note number
        note_number = cls._generate_note_number(tenant)
        
        # Create debit note
        debit_note = SupplierDebitNote.objects.create(
            tenant=tenant,
            bill=bill,
            debit_note_number=note_number,
            amount=amount,
            reason=reason,
            description=description or '',
            status='draft',
            issue_date=timezone.now().date(),
            submitted_by=created_by
        )
        
        return debit_note
    
    @classmethod
    @transaction.atomic
    def update_debit_note(cls, debit_note_id, tenant, amount=None, reason=None, description=None, updated_by=None):
        """
        Update draft debit note.
        
        Args:
            debit_note_id: UUID of debit note
            tenant: Tenant instance
            amount: Optional new amount
            reason: Optional new reason
            description: Optional new description
            updated_by: Person who updated
            
        Returns:
            Updated SupplierDebitNote instance
            
        Raises:
            ValidationError: If not in draft status or validation fails
        """
        debit_note = SupplierDebitNote.objects.select_for_update().get(
            id=debit_note_id,
            tenant=tenant
        )
        
        if debit_note.status != 'draft':
            raise ValidationError('Only draft debit notes can be updated.')
        
        if amount is not None:
            amount = Decimal(str(amount))
            if amount <= Decimal('0.00'):
                raise ValidationError('Debit note amount must be greater than zero.')
            debit_note.amount = amount
        
        if reason is not None:
            debit_note.reason = reason
        
        if description is not None:
            debit_note.description = description
        
        debit_note.save()
        return debit_note
    
    @classmethod
    @transaction.atomic
    def submit_debit_note(cls, debit_note_id, tenant, submitted_by=None):
        """
        Submit draft debit note for approval.
        
        Args:
            debit_note_id: UUID of debit note
            tenant: Tenant instance
            submitted_by: Person submitting the note
            
        Returns:
            Updated SupplierDebitNote instance
            
        Raises:
            ValidationError: If not in draft status
        """
        debit_note = SupplierDebitNote.objects.select_for_update().get(
            id=debit_note_id,
            tenant=tenant
        )
        
        if debit_note.status != 'draft':
            raise ValidationError('Only draft debit notes can be submitted.')
        
        debit_note.status = 'pending'
        debit_note.submitted_by = submitted_by
        debit_note.submitted_at = timezone.now()
        debit_note.save()
        
        return debit_note
    
    @classmethod
    @transaction.atomic
    def approve_debit_note(cls, debit_note_id, tenant, approved_by):
        """
        Approve submitted debit note and post accounting entries.
        
        This method performs:
        1. Status update to approved
        2. Increases supplier bill amount (debit increases payable)
        3. Updates supplier ledger (debit entry)
        4. Updates supplier balance
        5. Posts balanced journal entry (DR: Administrative Expenses, CR: Accounts Payable)
        
        Args:
            debit_note_id: UUID of debit note
            tenant: Tenant instance
            approved_by: Person instance approving the note (required)
            
        Returns:
            Approved SupplierDebitNote instance
            
        Raises:
            ValidationError: If not in pending status or validation fails
        """
        if not approved_by:
            raise ValidationError('Approver is required.')
        
        debit_note = SupplierDebitNote.objects.select_for_update().get(
            id=debit_note_id,
            tenant=tenant
        )
        
        if debit_note.status != 'pending':
            raise ValidationError('Only pending debit notes can be approved.')
        
        bill = SupplierBill.objects.select_for_update().get(id=debit_note.bill.id)
        
        # Update debit note status
        debit_note.status = 'approved'
        debit_note.approved_by = approved_by
        debit_note.approved_at = timezone.now()
        debit_note.save()
        
        # Increase bill amount (debit increases payable)
        bill.amount += debit_note.amount
        
        # Update bill status based on new amount vs paid amount
        if bill.paid_amount >= bill.amount:
            bill.status = 'paid'
        elif bill.paid_amount > Decimal('0.00'):
            bill.status = 'partial'
        else:
            bill.status = 'pending'
        bill.save()
        
        # Update supplier ledger (debit entry)
        cls._update_supplier_ledger(
            tenant=tenant,
            bill=bill,
            debit_note=debit_note,
            amount=debit_note.amount,
            transaction_type='debit'
        )
        
        # Update supplier balance
        cls._update_supplier_balance(tenant, bill.supplier_name, debit_note.amount, 'debit')
        
        # Post journal entry (DR: Administrative Expenses, CR: Accounts Payable)
        AutomaticAccountingIntegrationService.post_supplier_debit_note(
            tenant=tenant,
            reference_id=str(debit_note.id),
            amount=debit_note.amount
        )
        
        return debit_note
    
    @classmethod
    @transaction.atomic
    def reject_debit_note(cls, debit_note_id, tenant, rejected_by, rejection_reason):
        """
        Reject pending debit note and return to draft.
        
        Args:
            debit_note_id: UUID of debit note
            tenant: Tenant instance
            rejected_by: Person rejecting the note
            rejection_reason: Text reason for rejection (required)
            
        Returns:
            Rejected SupplierDebitNote instance
            
        Raises:
            ValidationError: If not in pending status or no reason provided
        """
        if not rejection_reason or not rejection_reason.strip():
            raise ValidationError('Rejection reason is required.')
        
        debit_note = SupplierDebitNote.objects.select_for_update().get(
            id=debit_note_id,
            tenant=tenant
        )
        
        if debit_note.status != 'pending':
            raise ValidationError('Only pending debit notes can be rejected.')
        
        debit_note.status = 'rejected'
        debit_note.rejected_by = rejected_by
        debit_note.rejected_at = timezone.now()
        debit_note.rejection_reason = rejection_reason
        debit_note.save()
        
        return debit_note
    
    @classmethod
    @transaction.atomic
    def cancel_debit_note(cls, debit_note_id, tenant, cancelled_by):
        """
        Cancel draft or rejected debit note.
        Approved debit notes cannot be cancelled (use reversal journal instead).
        
        Args:
            debit_note_id: UUID of debit note
            tenant: Tenant instance
            cancelled_by: Person cancelling the note
            
        Returns:
            Cancelled SupplierDebitNote instance
            
        Raises:
            ValidationError: If already approved or cancelled
        """
        debit_note = SupplierDebitNote.objects.select_for_update().get(
            id=debit_note_id,
            tenant=tenant
        )
        
        if debit_note.status == 'approved':
            raise ValidationError(
                'Approved debit notes cannot be cancelled. Use journal reversal instead.'
            )
        
        if debit_note.status == 'cancelled':
            raise ValidationError('Debit note is already cancelled.')
        
        debit_note.status = 'cancelled'
        debit_note.save()
        
        return debit_note
    
    @classmethod
    def get_debit_notes(cls, tenant, status=None, bill_id=None):
        """
        Retrieve debit notes with optional filtering.
        
        Args:
            tenant: Tenant instance
            status: Optional status filter
            bill_id: Optional bill ID filter
            
        Returns:
            QuerySet of SupplierDebitNote
        """
        queryset = SupplierDebitNote.objects.filter(tenant=tenant).select_related(
            'bill',
            'submitted_by',
            'approved_by',
            'rejected_by'
        )
        
        if status:
            queryset = queryset.filter(status=status)
        
        if bill_id:
            queryset = queryset.filter(bill_id=bill_id)
        
        return queryset.order_by('-issue_date', '-created_at')
    
    @classmethod
    def get_debit_note(cls, debit_note_id, tenant):
        """
        Retrieve single debit note with related data.
        
        Args:
            debit_note_id: UUID of debit note
            tenant: Tenant instance
            
        Returns:
            SupplierDebitNote instance
        """
        return SupplierDebitNote.objects.select_related(
            'bill',
            'submitted_by',
            'approved_by',
            'rejected_by'
        ).get(id=debit_note_id, tenant=tenant)
    
    @classmethod
    def _generate_note_number(cls, tenant):
        """
        Generate unique debit note number.
        Format: SDN-YYYYMMDD-XXXX
        
        Args:
            tenant: Tenant instance
            
        Returns:
            Unique note number string
        """
        today = timezone.now().date()
        date_prefix = today.strftime('%Y%m%d')
        
        last_note = SupplierDebitNote.objects.filter(
            tenant=tenant,
            debit_note_number__startswith=f'SDN-{date_prefix}'
        ).order_by('-debit_note_number').first()
        
        if last_note:
            try:
                last_seq = int(last_note.debit_note_number.split('-')[-1])
                new_seq = last_seq + 1
            except (IndexError, ValueError):
                new_seq = 1
        else:
            new_seq = 1
        
        return f'SDN-{date_prefix}-{new_seq:04d}'
    
    @classmethod
    def _update_supplier_ledger(cls, tenant, bill, debit_note, amount, transaction_type):
        """
        Create supplier ledger entry for debit note.
        
        Args:
            tenant: Tenant instance
            bill: SupplierBill instance
            debit_note: SupplierDebitNote instance
            amount: Decimal amount
            transaction_type: 'debit' for debit notes
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
        
        # Debit increases payable (add to balance)
        new_balance = current_balance + amount
        
        # Create ledger entry
        SupplierLedger.objects.create(
            tenant=tenant,
            supplier=supplier,
            transaction_date=debit_note.issue_date,
            description=f'Debit Note {debit_note.debit_note_number} - {debit_note.reason[:100]}',
            reference_number=debit_note.debit_note_number,
            debit_amount=amount,
            credit_amount=Decimal('0.00'),
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
            transaction_type: 'debit' for debit notes
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
        
        # Debit increases payable
        balance.current_balance += amount
        balance.last_transaction_date = timezone.now().date()
        balance.save()


class SupplierPaymentService:
    """
    Enterprise Supplier Payment Processing Service for EduOrbit ERP.
    Implements complete payment lifecycle: creation, approval, processing, voucher generation,
    withholding tax handling, supplier ledger updates, and automatic GL journal postings.
    Follows IFRS/IAS & GAAP accounting standards and Nigerian business regulations.
    """

    @classmethod
    @transaction.atomic
    def create_payment(cls, tenant, bill_id, amount, payment_method='bank_transfer', 
                      bank_account_id=None, description='', withholding_tax_rate=None, prepared_by=None):
        """
        Create a new supplier payment in draft status.
        
        Args:
            tenant: Tenant instance
            bill_id: UUID of SupplierBill
            amount: Decimal payment amount (gross amount)
            payment_method: Payment method choice
            bank_account_id: Optional bank account for payment
            description: Optional payment description
            withholding_tax_rate: Optional WHT rate (defaults to supplier's rate)
            prepared_by: Person instance who prepared the payment
            
        Returns:
            SupplierPayment instance
            
        Raises:
            ValidationError: If validation fails
            SupplierBill.DoesNotExist: If bill not found
        """
        bill = SupplierBill.objects.select_for_update().get(id=bill_id, tenant=tenant)
        amount = Decimal(str(amount))
        
        # Validation
        if amount <= Decimal('0.00'):
            raise ValidationError('Payment amount must be greater than zero.')
        
        if amount > bill.outstanding_amount:
            raise ValidationError(
                f'Payment amount (NGN {amount}) cannot exceed '
                f'outstanding bill amount (NGN {bill.outstanding_amount}).'
            )
        
        if bill.status == 'cancelled':
            raise ValidationError('Cannot create payment for cancelled bill.')
        
        # Get supplier for withholding tax calculation
        supplier = None
        wht_amount = Decimal('0.00')
        
        if withholding_tax_rate is None:
            supplier = Supplier.objects.filter(tenant=tenant, name=bill.supplier_name).first()
            if supplier:
                withholding_tax_rate = supplier.wht_rate
            else:
                withholding_tax_rate = Decimal('5.00')  # Default WHT rate
        
        # Calculate withholding tax
        if withholding_tax_rate and withholding_tax_rate > Decimal('0.00'):
            wht_amount = (amount * withholding_tax_rate) / Decimal('100.00')
        
        # Get bank account if specified
        bank_account = None
        if bank_account_id:
            bank_account = BankAccount.objects.get(id=bank_account_id, tenant=tenant)
        
        # Generate unique payment number and reference
        payment_number = cls._generate_payment_number(tenant)
        reference = cls._generate_payment_reference(tenant, payment_method)
        
        # Create payment
        payment = SupplierPayment.objects.create(
            tenant=tenant,
            bill=bill,
            payment_number=payment_number,
            amount=amount,
            payment_method=payment_method,
            reference=reference,
            payment_date=timezone.now(),
            status='draft',
            prepared_by=prepared_by,
            prepared_at=timezone.now(),
            bank_account=bank_account,
            description=description,
            withholding_tax_amount=wht_amount,
            net_amount=amount - wht_amount
        )
        
        return payment
    
    @classmethod
    @transaction.atomic
    def update_payment(cls, payment_id, tenant, amount=None, payment_method=None, 
                      bank_account_id=None, description=None, withholding_tax_rate=None, updated_by=None):
        """
        Update draft payment.
        
        Args:
            payment_id: UUID of payment
            tenant: Tenant instance
            amount: Optional new amount
            payment_method: Optional new payment method
            bank_account_id: Optional new bank account
            description: Optional new description
            withholding_tax_rate: Optional new WHT rate
            updated_by: Person who updated
            
        Returns:
            Updated SupplierPayment instance
            
        Raises:
            ValidationError: If not in draft status or validation fails
        """
        payment = SupplierPayment.objects.select_for_update().get(
            id=payment_id,
            tenant=tenant
        )
        
        if payment.status != 'draft':
            raise ValidationError('Only draft payments can be updated.')
        
        # Update amount and recalculate WHT if needed
        if amount is not None:
            amount = Decimal(str(amount))
            if amount <= Decimal('0.00'):
                raise ValidationError('Payment amount must be greater than zero.')
            
            if amount > payment.bill.outstanding_amount:
                raise ValidationError(
                    f'Payment amount (NGN {amount}) cannot exceed '
                    f'outstanding bill amount (NGN {payment.bill.outstanding_amount}).'
                )
            
            payment.amount = amount
            
            # Recalculate withholding tax
            if withholding_tax_rate is not None:
                wht_rate = Decimal(str(withholding_tax_rate))
            else:
                # Use existing rate or get from supplier
                supplier = Supplier.objects.filter(tenant=tenant, name=payment.bill.supplier_name).first()
                wht_rate = supplier.wht_rate if supplier else Decimal('5.00')
            
            payment.withholding_tax_amount = (amount * wht_rate) / Decimal('100.00')
            payment.net_amount = amount - payment.withholding_tax_amount
        
        if payment_method is not None:
            payment.payment_method = payment_method
        
        if bank_account_id is not None:
            bank_account = BankAccount.objects.get(id=bank_account_id, tenant=tenant)
            payment.bank_account = bank_account
        
        if description is not None:
            payment.description = description
        
        payment.save()
        return payment
    
    @classmethod
    @transaction.atomic
    def submit_payment_for_approval(cls, payment_id, tenant, submitted_by=None):
        """
        Submit draft payment for approval.
        
        Args:
            payment_id: UUID of payment
            tenant: Tenant instance
            submitted_by: Person submitting the payment
            
        Returns:
            Updated SupplierPayment instance
            
        Raises:
            ValidationError: If not in draft status
        """
        payment = SupplierPayment.objects.select_for_update().get(
            id=payment_id,
            tenant=tenant
        )
        
        if payment.status != 'draft':
            raise ValidationError('Only draft payments can be submitted for approval.')
        
        payment.status = 'pending'
        payment.save()
        
        return payment
    
    @classmethod
    @transaction.atomic
    def approve_payment(cls, payment_id, tenant, approved_by):
        """
        Approve pending payment and create payment voucher.
        
        Args:
            payment_id: UUID of payment
            tenant: Tenant instance
            approved_by: Person instance approving the payment (required)
            
        Returns:
            Dictionary with approved payment and created voucher
            
        Raises:
            ValidationError: If not in pending status or validation fails
        """
        if not approved_by:
            raise ValidationError('Approver is required.')
        
        payment = SupplierPayment.objects.select_for_update().get(
            id=payment_id,
            tenant=tenant
        )
        
        if payment.status != 'pending':
            raise ValidationError('Only pending payments can be approved.')
        
        # Update payment status
        payment.status = 'approved'
        payment.approved_by = approved_by
        payment.approved_at = timezone.now()
        payment.save()
        
        # Create payment voucher
        voucher = cls._create_payment_voucher(tenant, payment, approved_by)
        
        return {
            'payment': payment,
            'voucher': voucher
        }
    
    @classmethod
    @transaction.atomic
    def process_payment(cls, payment_id, tenant, processed_by, bank_reference=''):
        """
        Process approved payment and post accounting entries.
        
        This method performs:
        1. Status update to processed
        2. Updates supplier bill paid amount
        3. Updates supplier ledger (credit entry)
        4. Updates supplier balance
        5. Posts balanced journal entry (DR: Accounts Payable, CR: Cash & Bank)
        6. Posts withholding tax if applicable
        
        Args:
            payment_id: UUID of payment
            tenant: Tenant instance
            processed_by: Person instance processing the payment (required)
            bank_reference: Optional bank transaction reference
            
        Returns:
            Processed SupplierPayment instance
            
        Raises:
            ValidationError: If not in approved status or validation fails
        """
        if not processed_by:
            raise ValidationError('Processor is required.')
        
        payment = SupplierPayment.objects.select_for_update().get(
            id=payment_id,
            tenant=tenant
        )
        
        if payment.status != 'approved':
            raise ValidationError('Only approved payments can be processed.')
        
        bill = SupplierBill.objects.select_for_update().get(id=payment.bill.id)
        
        # Update payment status
        payment.status = 'processed'
        payment.processed_by = processed_by
        payment.processed_at = timezone.now()
        payment.bank_reference = bank_reference
        payment.save()
        
        # Update voucher status
        if hasattr(payment, 'voucher'):
            voucher = payment.voucher
            voucher.status = 'processed'
            voucher.processed_by = processed_by
            voucher.processed_at = timezone.now()
            voucher.save()
        
        # Update bill paid amount and status
        bill.paid_amount += payment.amount
        if bill.paid_amount >= bill.amount:
            bill.status = 'paid'
        elif bill.paid_amount > Decimal('0.00'):
            bill.status = 'partial'
        bill.save()
        
        # Update supplier ledger (credit entry for payment)
        cls._update_supplier_ledger(
            tenant=tenant,
            bill=bill,
            payment=payment,
            amount=payment.amount,
            transaction_type='payment'
        )
        
        # Update supplier balance
        cls._update_supplier_balance(tenant, bill.supplier_name, payment.amount, 'payment')
        
        # Post journal entry for payment (DR: Accounts Payable, CR: Cash & Bank)
        AutomaticAccountingIntegrationService.post_supplier_payment(
            tenant=tenant,
            reference_id=str(payment.id),
            amount=payment.amount
        )
        
        # Post withholding tax if applicable
        if payment.withholding_tax_amount > Decimal('0.00'):
            AutomaticAccountingIntegrationService.post_withholding_tax(
                tenant=tenant,
                reference_id=f"{payment.id}_WHT",
                amount=payment.withholding_tax_amount
            )
        
        return payment
    
    @classmethod
    @transaction.atomic
    def cancel_payment(cls, payment_id, tenant, cancelled_by):
        """
        Cancel draft or pending payment.
        Approved/processed payments cannot be cancelled (use reversal instead).
        
        Args:
            payment_id: UUID of payment
            tenant: Tenant instance
            cancelled_by: Person cancelling the payment
            
        Returns:
            Cancelled SupplierPayment instance
            
        Raises:
            ValidationError: If already processed or cancelled
        """
        payment = SupplierPayment.objects.select_for_update().get(
            id=payment_id,
            tenant=tenant
        )
        
        if payment.status in ['approved', 'processed']:
            raise ValidationError(
                'Approved or processed payments cannot be cancelled. Use reversal instead.'
            )
        
        if payment.status == 'cancelled':
            raise ValidationError('Payment is already cancelled.')
        
        payment.status = 'cancelled'
        payment.save()
        
        # Cancel voucher if exists
        if hasattr(payment, 'voucher'):
            voucher = payment.voucher
            voucher.status = 'cancelled'
            voucher.save()
        
        return payment
    
    @classmethod
    def get_payments(cls, tenant, status=None, bill_id=None, payment_method=None):
        """
        Retrieve payments with optional filtering.
        
        Args:
            tenant: Tenant instance
            status: Optional status filter
            bill_id: Optional bill ID filter
            payment_method: Optional payment method filter
            
        Returns:
            QuerySet of SupplierPayment
        """
        queryset = SupplierPayment.objects.filter(tenant=tenant).select_related(
            'bill',
            'prepared_by',
            'approved_by',
            'processed_by',
            'bank_account'
        )
        
        if status:
            queryset = queryset.filter(status=status)
        
        if bill_id:
            queryset = queryset.filter(bill_id=bill_id)
            
        if payment_method:
            queryset = queryset.filter(payment_method=payment_method)
        
        return queryset.order_by('-payment_date', '-created_at')
    
    @classmethod
    def get_payment(cls, payment_id, tenant):
        """
        Retrieve single payment with related data.
        
        Args:
            payment_id: UUID of payment
            tenant: Tenant instance
            
        Returns:
            SupplierPayment instance
        """
        return SupplierPayment.objects.select_related(
            'bill',
            'prepared_by',
            'approved_by', 
            'processed_by',
            'bank_account'
        ).get(id=payment_id, tenant=tenant)
    
    @classmethod
    def get_payment_vouchers(cls, tenant, status=None):
        """
        Retrieve payment vouchers with optional filtering.
        
        Args:
            tenant: Tenant instance
            status: Optional status filter
            
        Returns:
            QuerySet of PaymentVoucher
        """
        queryset = PaymentVoucher.objects.filter(tenant=tenant).select_related(
            'payment',
            'payment__bill',
            'prepared_by',
            'submitted_by',
            'approved_by',
            'processed_by'
        )
        
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.order_by('-prepared_at', '-created_at')
    
    @classmethod
    def get_payment_voucher(cls, voucher_id, tenant):
        """
        Retrieve single payment voucher with related data.
        
        Args:
            voucher_id: UUID of voucher
            tenant: Tenant instance
            
        Returns:
            PaymentVoucher instance
        """
        return PaymentVoucher.objects.select_related(
            'payment',
            'payment__bill',
            'prepared_by',
            'submitted_by',
            'approved_by',
            'processed_by'
        ).get(id=voucher_id, tenant=tenant)
    
    @classmethod
    def _generate_payment_number(cls, tenant):
        """
        Generate unique payment number.
        Format: PAY-YYYYMMDD-XXXX
        
        Args:
            tenant: Tenant instance
            
        Returns:
            Unique payment number string
        """
        today = timezone.now().date()
        date_prefix = today.strftime('%Y%m%d')
        
        last_payment = SupplierPayment.objects.filter(
            tenant=tenant,
            payment_number__startswith=f'PAY-{date_prefix}'
        ).order_by('-payment_number').first()
        
        if last_payment:
            try:
                last_seq = int(last_payment.payment_number.split('-')[-1])
                new_seq = last_seq + 1
            except (IndexError, ValueError):
                new_seq = 1
        else:
            new_seq = 1
        
        return f'PAY-{date_prefix}-{new_seq:04d}'
    
    @classmethod
    def _generate_payment_reference(cls, tenant, payment_method):
        """
        Generate unique payment reference based on method.
        
        Args:
            tenant: Tenant instance
            payment_method: Payment method choice
            
        Returns:
            Unique payment reference string
        """
        method_prefixes = {
            'bank_transfer': 'BT',
            'wire_transfer': 'WT',
            'ach_transfer': 'ACH',
            'cheque': 'CHQ',
            'cash': 'CASH',
            'electronic_payment': 'EP'
        }
        
        prefix = method_prefixes.get(payment_method, 'PAY')
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        unique_suffix = str(uuid.uuid4())[:8].upper()
        
        return f'{prefix}-{timestamp}-{unique_suffix}'
    
    @classmethod
    def _create_payment_voucher(cls, tenant, payment, approved_by):
        """
        Create payment voucher for approved payment.
        
        Args:
            tenant: Tenant instance
            payment: SupplierPayment instance
            approved_by: Person who approved
            
        Returns:
            PaymentVoucher instance
        """
        voucher_number = cls._generate_voucher_number(tenant)
        
        voucher = PaymentVoucher.objects.create(
            tenant=tenant,
            voucher_number=voucher_number,
            payment=payment,
            amount=payment.amount,
            prepared_by=payment.prepared_by,
            prepared_at=payment.prepared_at,
            submitted_by=approved_by,  # Same person who approved payment
            submitted_at=timezone.now(),
            approved_by=approved_by,
            approved_at=timezone.now(),
            status='approved',
            purpose=f'Payment for Bill #{payment.bill.bill_number} - {payment.bill.supplier_name}',
            beneficiary_name=payment.bill.supplier_name,
            beneficiary_account=payment.bank_account.account_number if payment.bank_account else '',
            beneficiary_bank=payment.bank_account.bank_name if payment.bank_account else '',
            supporting_documents=f'Supplier Bill #{payment.bill.bill_number}'
        )
        
        return voucher
    
    @classmethod
    def _generate_voucher_number(cls, tenant):
        """
        Generate unique voucher number.
        Format: PV-YYYYMMDD-XXXX
        
        Args:
            tenant: Tenant instance
            
        Returns:
            Unique voucher number string
        """
        today = timezone.now().date()
        date_prefix = today.strftime('%Y%m%d')
        
        last_voucher = PaymentVoucher.objects.filter(
            tenant=tenant,
            voucher_number__startswith=f'PV-{date_prefix}'
        ).order_by('-voucher_number').first()
        
        if last_voucher:
            try:
                last_seq = int(last_voucher.voucher_number.split('-')[-1])
                new_seq = last_seq + 1
            except (IndexError, ValueError):
                new_seq = 1
        else:
            new_seq = 1
        
        return f'PV-{date_prefix}-{new_seq:04d}'
    
    @classmethod
    def _update_supplier_ledger(cls, tenant, bill, payment, amount, transaction_type):
        """
        Create supplier ledger entry for payment.
        
        Args:
            tenant: Tenant instance
            bill: SupplierBill instance
            payment: SupplierPayment instance
            amount: Decimal amount
            transaction_type: 'payment' for payments
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
        
        # Payment reduces payable (subtract from balance)
        new_balance = current_balance - amount
        
        # Create ledger entry
        SupplierLedger.objects.create(
            tenant=tenant,
            supplier=supplier,
            transaction_date=payment.payment_date.date(),
            description=f'Payment {payment.payment_number} - {payment.description or "Bill Payment"}',
            reference_number=payment.payment_number,
            debit_amount=Decimal('0.00'),
            credit_amount=amount,
            balance_after=new_balance,
            bill=bill,
            payment=payment
        )
    
    @classmethod
    def _update_supplier_balance(cls, tenant, supplier_name, amount, transaction_type):
        """
        Update supplier balance for payment.
        
        Args:
            tenant: Tenant instance
            supplier_name: Name of supplier
            amount: Decimal amount
            transaction_type: 'payment' for payments
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
        
        # Payment reduces payable
        balance.total_payments += amount
        balance.current_balance = (
            balance.total_bills + 
            balance.total_debit_notes - 
            balance.total_credit_notes - 
            balance.total_payments
        )
        balance.last_transaction_date = timezone.now().date()
        balance.last_recalculated_at = timezone.now()
        balance.save()


