import uuid
from decimal import Decimal
from django.db import models
from django.utils import timezone
from backend.apps.core.models import TenantBaseModel, PlatformBaseModel, UUIDModel, TimestampModel, SoftDeleteModel, AuditModel, TenantManager

# ==============================================================
# FEE STRUCTURES & BILLING ITEMS
# ==============================================================

class FeeStructure(TenantBaseModel):
    """
    Standard billing items (Tuition, Exam Levies, Hostel Fees).
    """
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE)
    academic_year = models.ForeignKey('academic.AcademicYear', on_delete=models.CASCADE)
    name = models.CharField(max_length=150)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    category = models.CharField(max_length=50, default='tuition')

    def __str__(self):
        return f"{self.name} ({self.amount})"


class FeeRule(TenantBaseModel):
    """
    Scoping variables targeting specific classes or student categories.
    """
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.CASCADE, related_name='rules')
    academic_level = models.ForeignKey('academic.AcademicLevel', on_delete=models.SET_NULL, null=True, blank=True)
    boarding_status = models.CharField(max_length=30, default='both')  # boarding, day, both

    def __str__(self):
        return f"Rule for {self.fee_structure.name}"


class Invoice(TenantBaseModel):
    """
    Student outstanding bill statement headers.
    """
    STATUS = [
        ('draft', 'Draft'),
        ('issued', 'Issued'),
        ('partial', 'Partial Paid'),
        ('paid', 'Fully Paid'),
        ('cancelled', 'Cancelled')
    ]
    student = models.ForeignKey('people.StudentProfile', on_delete=models.CASCADE)
    invoice_number = models.CharField(max_length=100, unique=True)
    issue_date = models.DateField(default=timezone.now)
    due_date = models.DateField()
    status = models.CharField(max_length=30, choices=STATUS, default='draft')

    def __str__(self):
        return self.invoice_number


class InvoiceItem(TenantBaseModel):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.fee_structure.name}: {self.amount}"


# ==============================================================
# PAYMENTS, ALLOCATIONS, & PARENT WALLETS
# ==============================================================

class Payment(TenantBaseModel):
    """
    Cash, transfer, or wallet settlements logs.
    """
    invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=30, default='transfer')  # transfer, card, cash, wallet
    reference = models.CharField(max_length=100, unique=True)
    payment_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.reference} ({self.amount})"


class PaymentAllocation(TenantBaseModel):
    """
    Distributes one payment across multiple outstanding invoice items.
    """
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='allocations')
    invoice_item = models.ForeignKey(InvoiceItem, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"Allocated {self.amount} to {self.invoice_item}"


class StudentWallet(TenantBaseModel):
    """
    Pre-paid funds account held by a Parent or Student.
    """
    parent = models.ForeignKey('people.Person', on_delete=models.CASCADE, related_name='wallets', null=True, blank=True)
    student = models.ForeignKey('people.StudentProfile', on_delete=models.CASCADE, related_name='wallets', null=True, blank=True)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Wallet ({self.balance})"


class WalletTransaction(TenantBaseModel):
    wallet = models.ForeignKey(StudentWallet, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(max_length=20)  # credit, debit
    reference = models.CharField(max_length=100, blank=True, default='')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.transaction_type}: {self.amount}"


# ==============================================================
# DOUBLE-ENTRY GENERAL LEDGER
# ==============================================================

class StudentLedger(TenantBaseModel):
    """
    Immutable ledger entries keeping transaction audits.
    """
    student = models.ForeignKey('people.StudentProfile', on_delete=models.CASCADE)
    description = models.CharField(max_length=255)
    debit_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    credit_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2)
    reference_id = models.UUIDField(default=uuid.uuid4)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Ledger: {self.student.student_number} Bal: {self.balance_after}"


class JournalEvent(TenantBaseModel):
    event_type = models.CharField(max_length=100)  # e.g., fee_billing, payment_receive
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Event: {self.event_type}"


class JournalEntry(TenantBaseModel):
    event = models.ForeignKey(JournalEvent, on_delete=models.CASCADE, related_name='entries')
    account_name = models.CharField(max_length=150)  # e.g. Student Receivables, Cash
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    entry_type = models.CharField(max_length=10)  # debit, credit

    def __str__(self):
        return f"{self.entry_type.upper()}: {self.account_name} ({self.amount})"


class LedgerPosting(TenantBaseModel):
    entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE)
    posting_date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"Posting on {self.posting_date}"


# ==============================================================
# REFUNDS, CASHIERS, & INSTALLMENTS
# ==============================================================

class RefundRequest(TenantBaseModel):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, default='pending')  # pending, approved, paid
    reason = models.TextField()

    def __str__(self):
        return f"Refund: {self.amount} ({self.status})"


class CashierSession(TenantBaseModel):
    cashier = models.ForeignKey('people.Person', on_delete=models.CASCADE)
    opened_at = models.DateTimeField(default=timezone.now)
    closed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Session: {self.cashier.last_name}"


class InstallmentPlan(TenantBaseModel):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    total_installments = models.IntegerField(default=3)

    def __str__(self):
        return f"Plan for {self.invoice.invoice_number}"


class InstallmentSchedule(TenantBaseModel):
    plan = models.ForeignKey(InstallmentPlan, on_delete=models.CASCADE, related_name='schedules')
    due_date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"Due: {self.due_date} ({self.amount})"


# ==============================================================
# SAAS SUBSCRIPTIONS & PLATFORM REVENUE
# ==============================================================

class FinancialAid(TenantBaseModel):
    student = models.ForeignKey('people.StudentProfile', on_delete=models.CASCADE)
    aid_type = models.CharField(max_length=30)  # scholarship, discount, waiver, bursary
    percentage = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return f"{self.aid_type} for {self.student.student_number}"


class TenantSubscriptionInvoice(TenantBaseModel):
    """
    EduOrbit corporate subscriptions billed to school owners.
    """
    tenant_subscription = models.ForeignKey('tenants.TenantSubscription', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, default='unpaid')  # paid, unpaid

    def __str__(self):
        return f"SaaS bill: {self.amount} ({self.status})"


class PlatformCommission(TenantBaseModel):
    """
    Revenue share commissions subtracted from marketplace gateway cashouts.
    """
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE)
    commission_amount = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"Commission: {self.commission_amount}"


# ==============================================================
# ENTERPRISE BUDGETING & FINANCIAL CONTROL
# ==============================================================

class Budget(TenantBaseModel):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('frozen', 'Frozen')
    ]
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE)
    academic_year = models.ForeignKey('academic.AcademicYear', on_delete=models.CASCADE)
    name = models.CharField(max_length=150)
    total_allocated = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_committed = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_spent = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='draft')

    def __str__(self):
        return f"{self.name} ({self.status})"


class BudgetItem(TenantBaseModel):
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='items')
    category_name = models.CharField(max_length=100)  # e.g., IT Hardware, Operating Supplies
    allocated_amount = models.DecimalField(max_digits=12, decimal_places=2)
    committed_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    spent_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.category_name}: ${self.spent_amount} / ${self.allocated_amount}"


# ==============================================================
# ACCOUNTS PAYABLE & SUPPLIER MANAGEMENT
# ==============================================================

class SupplierBill(TenantBaseModel):
    """
    Vendor invoice and supplier bill tracking.
    Enforces tenant isolation, decimal precision (12,2), status choices, and audit constraints.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('partial', 'Partially Paid'),
        ('paid', 'Fully Paid'),
        ('cancelled', 'Cancelled')
    ]
    supplier_name = models.CharField(max_length=150)
    bill_number = models.CharField(max_length=100, unique=True, db_index=True)
    issue_date = models.DateField(default=timezone.now, db_index=True)
    due_date = models.DateField(db_index=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending', db_index=True)
    category = models.CharField(max_length=100, default='General Supplies')

    class Meta:
        indexes = [
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['tenant', 'due_date']),
            models.Index(fields=['supplier_name']),
        ]

    def __str__(self):
        return f"Bill #{self.bill_number} - {self.supplier_name} (${self.amount})"

    @property
    def outstanding_amount(self):
        return self.amount - self.paid_amount

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.amount is not None and self.amount <= Decimal('0.00'):
            raise ValidationError({'amount': 'Supplier bill amount must be greater than zero.'})
        if self.paid_amount is not None and self.paid_amount < Decimal('0.00'):
            raise ValidationError({'paid_amount': 'Paid amount cannot be negative.'})
        if self.amount is not None and self.paid_amount is not None and self.paid_amount > self.amount:
            raise ValidationError({'paid_amount': 'Paid amount cannot exceed total bill amount.'})
        if self.due_date and self.issue_date and self.due_date < self.issue_date:
            raise ValidationError({'due_date': 'Due date cannot be earlier than issue date.'})



class SupplierPayment(TenantBaseModel):
    """
    Enterprise Outward Cash Disbursement Records to Vendors.
    Enforces tenant isolation, decimal precision (12,2), approval workflow, and GL integration.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('processed', 'Bank Processed'),
        ('cancelled', 'Cancelled')
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('bank_transfer', 'Bank Transfer'),
        ('wire_transfer', 'Wire Transfer'),
        ('ach_transfer', 'ACH Transfer'),
        ('cheque', 'Cheque Payment'),
        ('cash', 'Cash Payment'),
        ('electronic_payment', 'Electronic Payment')
    ]
    
    bill = models.ForeignKey(SupplierBill, on_delete=models.CASCADE, related_name='payments')
    payment_number = models.CharField(max_length=100, unique=True, db_index=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=30, choices=PAYMENT_METHOD_CHOICES, default='bank_transfer')
    reference = models.CharField(max_length=100, unique=True, db_index=True)
    payment_date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', db_index=True)
    
    # Enterprise workflow fields
    prepared_by = models.ForeignKey('people.Person', on_delete=models.SET_NULL, null=True, blank=True, related_name='prepared_payments')
    approved_by = models.ForeignKey('people.Person', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_payments')
    processed_by = models.ForeignKey('people.Person', on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_payments')
    
    # Timestamp tracking
    prepared_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    # Bank details
    bank_account = models.ForeignKey('BankAccount', on_delete=models.SET_NULL, null=True, blank=True, related_name='supplier_payments')
    bank_reference = models.CharField(max_length=100, blank=True, default='')
    
    # Additional details
    description = models.TextField(blank=True, default='')
    withholding_tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    net_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['tenant', 'payment_date']),
            models.Index(fields=['payment_number']),
            models.Index(fields=['reference']),
        ]
        ordering = ['-payment_date', '-created_at']

    def __str__(self):
        return f"Payment #{self.payment_number} (NGN {self.amount})"
    
    def save(self, *args, **kwargs):
        # Calculate net amount if not provided
        if self.net_amount is None:
            self.net_amount = self.amount - self.withholding_tax_amount
        super().save(*args, **kwargs)
    
    def clean(self):
        from django.core.exceptions import ValidationError
        if self.amount is not None and self.amount <= Decimal('0.00'):
            raise ValidationError({'amount': 'Payment amount must be greater than zero.'})
        
        if self.withholding_tax_amount is not None and self.withholding_tax_amount < Decimal('0.00'):
            raise ValidationError({'withholding_tax_amount': 'Withholding tax amount cannot be negative.'})
        
        if self.amount is not None and self.withholding_tax_amount is not None:
            if self.withholding_tax_amount > self.amount:
                raise ValidationError({'withholding_tax_amount': 'Withholding tax cannot exceed payment amount.'})


# ==============================================================
# BANK MANAGEMENT & RECONCILIATION
# ==============================================================

class BankAccount(TenantBaseModel):
    """
    School Bank and Cash Treasury accounts.
    """
    ACCOUNT_TYPE_CHOICES = [
        ('bank', 'Bank Account'),
        ('cash', 'Cash Till / Vault')
    ]
    account_name = models.CharField(max_length=150)
    account_number = models.CharField(max_length=50)
    bank_name = models.CharField(max_length=100, default='Central Treasury Bank')
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES, default='bank')
    opening_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    current_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=10, default='NGN')

    def __str__(self):
        return f"{self.bank_name} - {self.account_name} ({self.account_number})"


class BankStatementItem(TenantBaseModel):
    """
    Imported bank statement transaction lines.
    """
    bank_account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name='statement_items')
    transaction_date = models.DateField(default=timezone.now)
    description = models.CharField(max_length=255)
    reference = models.CharField(max_length=100)
    debit_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    credit_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    is_reconciled = models.BooleanField(default=False)

    def __str__(self):
        return f"Stmt Item #{self.reference}: Dr {self.debit_amount} / Cr {self.credit_amount}"


class ChequeRegister(TenantBaseModel):
    """
    Cheque book issuance and clearing register.
    """
    STATUS_CHOICES = [
        ('issued', 'Issued'),
        ('cleared', 'Cleared'),
        ('cancelled', 'Cancelled'),
        ('bounced', 'Bounced')
    ]
    bank_account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name='cheques')
    cheque_number = models.CharField(max_length=50, unique=True)
    payee_name = models.CharField(max_length=150)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    issue_date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='issued')

    def __str__(self):
        return f"Cheque #{self.cheque_number} to {self.payee_name} (${self.amount})"


# ==============================================================
# ENTERPRISE ACCOUNTS RECEIVABLE (AR) ADVANCED MODULES
# ==============================================================

class CreditNote(TenantBaseModel):
    """
    Credit Note reducing Student / Customer Accounts Receivable balance.
    """
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='credit_notes')
    note_number = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.CharField(max_length=255)
    issue_date = models.DateTimeField(default=timezone.now)
    is_approved = models.BooleanField(default=True)

    def __str__(self):
        return f"Credit Note #{self.note_number} (${self.amount})"


class DebitNote(TenantBaseModel):
    """
    Debit Note increasing Student / Customer Accounts Receivable balance (e.g. penalty, late charge).
    """
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='debit_notes')
    note_number = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.CharField(max_length=255)
    issue_date = models.DateTimeField(default=timezone.now)
    is_approved = models.BooleanField(default=True)

    def __str__(self):
        return f"Debit Note #{self.note_number} (${self.amount})"


class BadDebtWriteOff(TenantBaseModel):
    """
    Bad debt provision and uncollectible receivable write-off record.
    """
    STATUS_CHOICES = [
        ('provisioned', 'Bad Debt Provisioned'),
        ('approved', 'Written Off'),
        ('rejected', 'Write-Off Rejected')
    ]
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='write_offs')
    write_off_number = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.CharField(max_length=255)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='provisioned')
    approved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Write-Off #{self.write_off_number} (${self.amount}) - {self.status}"


class CustomerBalanceConfirmation(TenantBaseModel):
    """
    Auditor customer & parent balance confirmation letter log.
    """
    student = models.ForeignKey('people.StudentProfile', on_delete=models.CASCADE, null=True, blank=True)
    confirmation_number = models.CharField(max_length=100, unique=True)
    confirmed_balance = models.DecimalField(max_digits=12, decimal_places=2)
    as_of_date = models.DateField(default=timezone.now)
    is_confirmed = models.BooleanField(default=False)
    confirmation_notes = models.TextField(blank=True, default='')

    def __str__(self):
        return f"Balance Conf #{self.confirmation_number} (${self.confirmed_balance})"


# ==============================================================
# ENTERPRISE ACCOUNTS PAYABLE (AP) ADVANCED MODULES
# ==============================================================

class Supplier(UUIDModel, TimestampModel, SoftDeleteModel, AuditModel):
    """
    Vendor & Supplier profile record with Tax & WHT properties.
    Override tenant field to avoid conflict with inventory.Supplier.
    """
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name="efbm_suppliers",
        db_index=True
    )
    name = models.CharField(max_length=150)
    tax_id = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    wht_rate = models.DecimalField(max_digits=5, decimal_places=2, default=5.00)  # Withholding Tax %

    # Use TenantManager for soft delete functionality
    objects = TenantManager()
    all_objects = models.Manager()

    class Meta:
        indexes = [
            models.Index(fields=['tenant', 'is_deleted']),
        ]

    def __str__(self):
        return self.name


class SupplierCreditNote(TenantBaseModel):
    """
    Supplier Credit Note reducing Accounts Payable liability.
    Enforces tenant isolation, decimal precision (12,2), approval workflow, and GL integration.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled')
    ]
    
    bill = models.ForeignKey(SupplierBill, on_delete=models.CASCADE, related_name='credit_notes', db_index=True)
    note_number = models.CharField(max_length=100, unique=True, db_index=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', db_index=True)
    issue_date = models.DateField(default=timezone.now, db_index=True)
    approved_by = models.ForeignKey('people.Person', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_credit_notes')
    approved_at = models.DateTimeField(null=True, blank=True)
    submitted_by = models.ForeignKey('people.Person', on_delete=models.SET_NULL, null=True, blank=True, related_name='submitted_credit_notes')
    submitted_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, default='')
    
    class Meta:
        indexes = [
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['tenant', 'issue_date']),
            models.Index(fields=['bill', 'status']),
        ]
        ordering = ['-issue_date', '-created_at']

    def __str__(self):
        return f"Supplier Credit Note #{self.note_number} (NGN {self.amount})"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        if self.amount is not None and self.amount <= Decimal('0.00'):
            raise ValidationError({'amount': 'Credit note amount must be greater than zero.'})
        if self.bill and self.amount and self.amount > self.bill.outstanding_amount:
            raise ValidationError({'amount': f'Credit note amount (NGN {self.amount}) cannot exceed bill outstanding amount (NGN {self.bill.outstanding_amount}).'})
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class SupplierDebitNote(TenantBaseModel):
    """
    Supplier Debit Note increasing Accounts Payable liability.
    Enforces tenant isolation, decimal precision (12,2), approval workflow, and GL integration.
    Used for: freight adjustments, price increases, under-billing corrections, tax adjustments, penalties.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled')
    ]
    
    bill = models.ForeignKey(SupplierBill, on_delete=models.CASCADE, related_name='debit_notes', db_index=True)
    debit_note_number = models.CharField(max_length=100, unique=True, db_index=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.TextField()
    description = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', db_index=True)
    issue_date = models.DateField(default=timezone.now, db_index=True)
    
    # Approval workflow fields
    submitted_by = models.ForeignKey('people.Person', on_delete=models.SET_NULL, null=True, blank=True, related_name='submitted_debit_notes')
    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey('people.Person', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_debit_notes')
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_by = models.ForeignKey('people.Person', on_delete=models.SET_NULL, null=True, blank=True, related_name='rejected_debit_notes')
    rejected_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, default='')
    
    class Meta:
        indexes = [
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['tenant', 'issue_date']),
            models.Index(fields=['bill', 'status']),
            models.Index(fields=['debit_note_number']),
        ]
        ordering = ['-issue_date', '-created_at']

    def __str__(self):
        return f"Supplier Debit Note #{self.debit_note_number} (NGN {self.amount})"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        if self.amount is not None and self.amount <= Decimal('0.00'):
            raise ValidationError({'amount': 'Debit note amount must be greater than zero.'})
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property 
    def note_number(self):
        """Backward compatibility property"""
        return self.debit_note_number


class PaymentVoucher(TenantBaseModel):
    """
    Enterprise Payment Voucher for Official Cash & Bank Disbursements.
    Complete workflow from draft creation to bank processing with approval controls.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('processed', 'Bank Processed'),
        ('cancelled', 'Cancelled')
    ]
    
    voucher_number = models.CharField(max_length=100, unique=True, db_index=True)
    payment = models.OneToOneField(SupplierPayment, on_delete=models.CASCADE, related_name='voucher')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Enterprise workflow fields
    prepared_by = models.ForeignKey('people.Person', on_delete=models.SET_NULL, null=True, blank=True, related_name='prepared_vouchers')
    submitted_by = models.ForeignKey('people.Person', on_delete=models.SET_NULL, null=True, blank=True, related_name='submitted_vouchers')
    approved_by = models.ForeignKey('people.Person', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_vouchers')
    rejected_by = models.ForeignKey('people.Person', on_delete=models.SET_NULL, null=True, blank=True, related_name='rejected_vouchers')
    processed_by = models.ForeignKey('people.Person', on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_vouchers')
    
    # Timestamp tracking
    prepared_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', db_index=True)
    
    # Approval and processing details
    purpose = models.TextField(blank=True, default='')
    beneficiary_name = models.CharField(max_length=200, blank=True, default='')
    beneficiary_account = models.CharField(max_length=50, blank=True, default='')
    beneficiary_bank = models.CharField(max_length=100, blank=True, default='')
    
    # Rejection handling
    rejection_reason = models.TextField(blank=True, default='')
    
    # Supporting documents
    supporting_documents = models.TextField(blank=True, default='', 
                                          help_text='List of supporting documents (invoices, receipts, etc.)')
    
    class Meta:
        indexes = [
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['voucher_number']),
            models.Index(fields=['tenant', 'prepared_at']),
        ]
        ordering = ['-prepared_at', '-created_at']

    def __str__(self):
        return f"Payment Voucher #{self.voucher_number} (NGN {self.amount})"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        if self.amount is not None and self.amount <= Decimal('0.00'):
            raise ValidationError({'amount': 'Voucher amount must be greater than zero.'})


class PaymentBatch(TenantBaseModel):
    """
    Batch payment run combining multiple supplier payments for bank transfer processing.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft Batch'),
        ('approved', 'Approved Batch'),
        ('processed', 'Bank Processed')
    ]
    batch_number = models.CharField(max_length=100, unique=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='draft')
    payment_date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"Payment Batch #{self.batch_number} (${self.total_amount})"


class SupplierRefund(TenantBaseModel):
    """
    Supplier refund record receiving funds back from vendors.
    """
    refund_number = models.CharField(max_length=100, unique=True)
    supplier_name = models.CharField(max_length=150)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.CharField(max_length=255)
    issue_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Supplier Refund #{self.refund_number} (${self.amount})"


# ==============================================================
# MISSING ACCOUNTS PAYABLE MODELS - ENTERPRISE ADDITIONS
# ==============================================================

class SupplierLedger(TenantBaseModel):
    """
    Individual supplier transaction sub-ledger tracking vendor debits, credits, and running balance.
    Follows EduOrbit multi-tenant architecture and IFRS sub-ledger control standards.
    """
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='ledger_entries')
    transaction_date = models.DateField(default=timezone.now, db_index=True)
    description = models.CharField(max_length=255)
    reference_number = models.CharField(max_length=100, db_index=True)
    debit_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    credit_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    balance_after = models.DecimalField(max_digits=12, decimal_places=2)
    bill = models.ForeignKey(SupplierBill, on_delete=models.SET_NULL, null=True, blank=True, related_name='ledger_postings')
    payment = models.ForeignKey(SupplierPayment, on_delete=models.SET_NULL, null=True, blank=True, related_name='ledger_postings')

    class Meta:
        ordering = ['-transaction_date', '-created_at']
        indexes = [
            models.Index(fields=['tenant', 'transaction_date']),
            models.Index(fields=['supplier', 'transaction_date']),
            models.Index(fields=['reference_number']),
        ]

    def __str__(self):
        return f"SupplierLedger: {self.supplier.name} - {self.description} (${self.balance_after})"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.debit_amount is not None and self.debit_amount < Decimal('0.00'):
            raise ValidationError({'debit_amount': 'Debit amount cannot be negative.'})
        if self.credit_amount is not None and self.credit_amount < Decimal('0.00'):
            raise ValidationError({'credit_amount': 'Credit amount cannot be negative.'})
        if self.debit_amount == Decimal('0.00') and self.credit_amount == Decimal('0.00'):
            raise ValidationError({'debit_amount': 'Supplier ledger entry must contain a non-zero debit or credit amount.'})



class ApprovalMatrix(TenantBaseModel):
    """
    Multi-level approval matrix configuration for supplier bills based on monetary thresholds.
    Configures one-level, two-level, or three-level approval matrices (e.g. $0-$100k, $100k-$1M, >$1M).
    """
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    min_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    max_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    category = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Approval Matrix"
        verbose_name_plural = "Approval Matrices"
        ordering = ['min_amount']
        indexes = [
            models.Index(fields=['tenant', 'is_active', 'min_amount']),
        ]

    def __str__(self):
        max_str = f"${self.max_amount}" if self.max_amount else "Unlimited"
        return f"Approval Matrix: {self.name} (${self.min_amount} - {max_str})"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.min_amount is not None and self.min_amount < Decimal('0.00'):
            raise ValidationError({'min_amount': 'Minimum amount cannot be negative.'})
        if self.max_amount is not None and self.max_amount < Decimal('0.00'):
            raise ValidationError({'max_amount': 'Maximum amount cannot be negative.'})
        if self.min_amount is not None and self.max_amount is not None and self.max_amount < self.min_amount:
            raise ValidationError({'max_amount': 'Maximum amount cannot be less than minimum amount.'})


class ApprovalLevel(TenantBaseModel):
    """
    Individual approval level within an approval matrix (Level 1: Finance Officer, Level 2: Finance Manager, Level 3: CFO).
    """
    APPROVAL_TYPE_CHOICES = [
        ('user', 'Specific User'),
        ('role', 'User Role'),
        ('department', 'Department Head'),
        ('amount_based', 'Amount-Based Rule')
    ]
    
    approval_matrix = models.ForeignKey(ApprovalMatrix, on_delete=models.CASCADE, related_name='levels')
    level_order = models.IntegerField()  # 1, 2, 3, etc.
    approval_type = models.CharField(max_length=20, choices=APPROVAL_TYPE_CHOICES, default='role')
    approver_user = models.ForeignKey('people.Person', on_delete=models.SET_NULL, null=True, blank=True)
    approver_role = models.CharField(max_length=100, blank=True)
    is_required = models.BooleanField(default=True)
    can_delegate = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Approval Level"
        verbose_name_plural = "Approval Levels"
        ordering = ['approval_matrix', 'level_order']
        constraints = [
            models.UniqueConstraint(fields=['tenant', 'approval_matrix', 'level_order'], name='unique_approval_level_order_per_matrix')
        ]
        indexes = [
            models.Index(fields=['approval_matrix', 'level_order']),
        ]

    def __str__(self):
        role_or_user = self.approver_user or self.approver_role or self.approval_type
        return f"Level {self.level_order} ({self.approval_matrix.name}): {role_or_user}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.level_order < 1:
            raise ValidationError({'level_order': 'Level order must be 1 or greater.'})


class BillApproval(TenantBaseModel):
    """
    Individual approval execution log for supplier bills tracking multi-level sign-offs.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('delegated', 'Delegated')
    ]
    
    bill = models.ForeignKey(SupplierBill, on_delete=models.CASCADE, related_name='approvals')
    approval_level = models.ForeignKey(ApprovalLevel, on_delete=models.CASCADE)
    approver = models.ForeignKey('people.Person', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approval_date = models.DateTimeField(null=True, blank=True)
    comments = models.TextField(blank=True)
    delegated_to = models.ForeignKey('people.Person', on_delete=models.SET_NULL, null=True, blank=True, related_name='delegated_approvals')

    class Meta:
        verbose_name = "Bill Approval"
        verbose_name_plural = "Bill Approvals"
        ordering = ['approval_level__level_order']
        constraints = [
            models.UniqueConstraint(fields=['tenant', 'bill', 'approval_level'], name='unique_bill_approval_level_per_bill')
        ]
        indexes = [
            models.Index(fields=['tenant', 'bill', 'status']),
            models.Index(fields=['approver', 'status']),
        ]

    def __str__(self):
        return f"Bill Approval #{self.bill.bill_number} - Level {self.approval_level.level_order} ({self.status})"



class RecurringSupplierBill(TenantBaseModel):
    """
    Template for automatically generating recurring supplier bills.
    """
    FREQUENCY_CHOICES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('semi_annually', 'Semi-Annually'),
        ('annually', 'Annually'),
        ('weekly', 'Weekly')
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled')
    ]
    
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='recurring_bills')
    template_name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    category = models.CharField(max_length=100, default='General Supplies')
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='monthly')
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)
    next_generation_date = models.DateField()
    payment_terms_days = models.IntegerField(default=30)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    auto_approve = models.BooleanField(default=False)

    def __str__(self):
        return f"Recurring: {self.template_name} - {self.supplier.name} ({self.frequency})"


class SupplierBalance(TenantBaseModel):
    """
    Maintains the current financial position of every supplier for AP control account summary.
    Updated whenever supplier transactions (Bills, Debit Notes, Credit Notes, Payments) occur.
    """
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='balance')
    current_balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_bills = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_payments = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_credit_notes = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_debit_notes = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    last_transaction_date = models.DateField(null=True, blank=True, db_index=True)
    last_recalculated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Supplier Balance"
        verbose_name_plural = "Supplier Balances"
        ordering = ['-last_recalculated_at']
        constraints = [
            models.UniqueConstraint(fields=['tenant', 'supplier'], name='unique_supplier_balance_per_tenant')
        ]
        indexes = [
            models.Index(fields=['tenant', 'supplier']),
            models.Index(fields=['tenant', 'current_balance']),
            models.Index(fields=['last_transaction_date']),
        ]

    def __str__(self):
        return f"SupplierBalance: {self.supplier.name} (${self.current_balance})"

    @property
    def is_in_credit(self):
        return self.current_balance < Decimal('0.00')

    @property
    def is_in_debt(self):
        return self.current_balance > Decimal('0.00')

    def clean(self):
        from django.core.exceptions import ValidationError
        monetary_fields = {
            'total_bills': self.total_bills,
            'total_payments': self.total_payments,
            'total_credit_notes': self.total_credit_notes,
            'total_debit_notes': self.total_debit_notes
        }
        for field_name, value in monetary_fields.items():
            if value is not None and value < Decimal('0.00'):
                raise ValidationError({field_name: f'{field_name.replace("_", " ").title()} cannot be negative.'})



class PaymentBatchItem(TenantBaseModel):
    """
    Individual payment items within a batch payment run.
    """
    STATUS_CHOICES = [
        ('included', 'Included'),
        ('excluded', 'Excluded'),
        ('processed', 'Processed'),
        ('failed', 'Failed')
    ]
    
    payment_batch = models.ForeignKey(PaymentBatch, on_delete=models.CASCADE, related_name='items')
    supplier_payment = models.ForeignKey(SupplierPayment, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='included')
    bank_reference = models.CharField(max_length=100, blank=True)
    processing_notes = models.TextField(blank=True)

    def __str__(self):
        return f"Batch Item: {self.payment_batch.batch_number} - ${self.amount} ({self.status})"


class WithholdingTaxEntry(TenantBaseModel):
    """
    Withholding tax calculations and tracking for supplier payments.
    """
    TAX_TYPE_CHOICES = [
        ('wht_services', 'WHT on Services'),
        ('wht_goods', 'WHT on Goods'),
        ('vat', 'VAT'),
        ('contractor_tax', 'Contractor Tax'),
        ('professional_tax', 'Professional Services Tax')
    ]
    
    supplier_payment = models.ForeignKey(SupplierPayment, on_delete=models.CASCADE, related_name='withholding_taxes')
    tax_type = models.CharField(max_length=30, choices=TAX_TYPE_CHOICES, default='wht_services')
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2)  # e.g., 5.00 for 5%
    taxable_amount = models.DecimalField(max_digits=12, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2)
    tax_authority = models.CharField(max_length=100, default='FIRS')
    certificate_number = models.CharField(max_length=100, blank=True)
    remittance_date = models.DateField(null=True, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['supplier_payment', 'tax_type']),
            models.Index(fields=['remittance_date']),
        ]

    def __str__(self):
        return f"WHT: {self.tax_type} - ${self.tax_amount} ({self.tax_rate}%)"


class SupplierStatement(TenantBaseModel):
    """
    Stores generated supplier statements for a defined reporting period.
    Supports statement generation, PDF/Excel exports, audit history, and statement regeneration.
    """
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='statements')
    statement_number = models.CharField(max_length=150, unique=True, db_index=True)
    statement_start_date = models.DateField(db_index=True)
    statement_end_date = models.DateField(db_index=True)
    opening_balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_debits = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_credits = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    closing_balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    generated_at = models.DateTimeField(default=timezone.now, db_index=True)
    generated_by = models.UUIDField(null=True, blank=True)
    pdf_file = models.FileField(upload_to='supplier_statements/pdf/', null=True, blank=True)
    excel_file = models.FileField(upload_to='supplier_statements/excel/', null=True, blank=True)
    is_finalized = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Supplier Statement"
        verbose_name_plural = "Supplier Statements"
        ordering = ['-generated_at']
        constraints = [
            models.UniqueConstraint(
                fields=['tenant', 'supplier', 'statement_start_date', 'statement_end_date'],
                name='unique_supplier_statement_per_period'
            )
        ]
        indexes = [
            models.Index(fields=['tenant', 'supplier']),
            models.Index(fields=['generated_at']),
            models.Index(fields=['statement_number']),
            models.Index(fields=['statement_start_date', 'statement_end_date']),
        ]

    def __str__(self):
        period_str = self.statement_start_date.strftime('%b %Y') if self.statement_start_date else ''
        return f"Statement #{self.statement_number} - {self.supplier.name} ({period_str})"

    @property
    def statement_period(self):
        if self.statement_start_date and self.statement_end_date:
            return f"{self.statement_start_date.strftime('%d %b %Y')} - {self.statement_end_date.strftime('%d %b %Y')}"
        return ""

    @property
    def transaction_count(self):
        from backend.apps.efbm.models import SupplierLedger
        return SupplierLedger.objects.filter(
            tenant=self.tenant,
            supplier=self.supplier,
            transaction_date__gte=self.statement_start_date,
            transaction_date__lte=self.statement_end_date
        ).count()

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.statement_start_date and self.statement_end_date and self.statement_end_date < self.statement_start_date:
            raise ValidationError({'statement_end_date': 'Statement end date cannot be earlier than statement start date.'})
        if self.opening_balance is not None and self.opening_balance < Decimal('0.00'):
            raise ValidationError({'opening_balance': 'Opening balance cannot be negative.'})
        if self.total_debits is not None and self.total_debits < Decimal('0.00'):
            raise ValidationError({'total_debits': 'Total debits cannot be negative.'})
        if self.total_credits is not None and self.total_credits < Decimal('0.00'):
            raise ValidationError({'total_credits': 'Total credits cannot be negative.'})
        
        # Check closing balance consistency: Opening + Debits - Credits = Closing
        if all(v is not None for v in [self.opening_balance, self.total_debits, self.total_credits, self.closing_balance]):
            expected_closing = self.opening_balance + self.total_debits - self.total_credits
            if self.closing_balance != expected_closing:
                raise ValidationError({'closing_balance': f'Closing balance (${self.closing_balance}) does not equal Opening (${self.opening_balance}) + Debits (${self.total_debits}) - Credits (${self.total_credits}) = ${expected_closing}.'})



class SupplierAgingBucket(TenantBaseModel):
    """
    Snapshot of supplier aging analysis for historical tracking.
    """
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='aging_snapshots')
    snapshot_date = models.DateField(default=timezone.now)
    current_0_30 = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    days_31_60 = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    days_61_90 = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    days_over_90 = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_outstanding = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    class Meta:
        ordering = ['-snapshot_date']
        unique_together = ['supplier', 'snapshot_date']

    def __str__(self):
        return f"Aging: {self.supplier.name} ({self.snapshot_date}) - ${self.total_outstanding}"


class PaymentSchedule(TenantBaseModel):
    """
    Scheduled future payments for supplier bills.
    """
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('processed', 'Processed'),
        ('cancelled', 'Cancelled'),
        ('failed', 'Failed')
    ]
    
    supplier_bill = models.ForeignKey(SupplierBill, on_delete=models.CASCADE, related_name='payment_schedules')
    scheduled_date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=30, default='bank_transfer')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey('people.Person', on_delete=models.SET_NULL, null=True, blank=True)
    processed_date = models.DateTimeField(null=True, blank=True)
    payment_reference = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['scheduled_date']

    def __str__(self):
        return f"Scheduled Payment: {self.supplier_bill.bill_number} - ${self.amount} ({self.scheduled_date})"


class SupplierPerformanceMetric(TenantBaseModel):
    """
    Vendor performance statistics and KPIs for supplier evaluation.
    """
    supplier = models.OneToOneField(Supplier, on_delete=models.CASCADE, related_name='performance_metrics')
    total_transactions = models.IntegerField(default=0)
    total_amount_transacted = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    average_payment_days = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    on_time_payment_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)  # Percentage
    dispute_count = models.IntegerField(default=0)
    credit_note_count = models.IntegerField(default=0)
    debit_note_count = models.IntegerField(default=0)
    last_payment_date = models.DateField(null=True, blank=True)
    preferred_payment_method = models.CharField(max_length=50, blank=True)
    quality_rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)  # 1.00 - 5.00
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Performance: {self.supplier.name} - {self.on_time_payment_rate}% on-time"


# ==============================================================
# AUDIT TRAIL MODELS
# ==============================================================

class SupplierBillAudit(TenantBaseModel):
    """
    Audit trail for all changes to supplier bills.
    """
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('paid', 'Payment Recorded'),
        ('cancelled', 'Cancelled'),
        ('deleted', 'Deleted')
    ]
    
    supplier_bill = models.ForeignKey(SupplierBill, on_delete=models.CASCADE, related_name='audit_trail')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    user = models.ForeignKey('people.Person', on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    old_values = models.JSONField(null=True, blank=True)  # Previous state
    new_values = models.JSONField(null=True, blank=True)  # New state
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"Audit: {self.supplier_bill.bill_number} - {self.action} by {self.user}"


class PaymentReversalLog(TenantBaseModel):
    """
    Log of payment reversals with detailed tracking.
    """
    original_payment = models.OneToOneField(SupplierPayment, on_delete=models.CASCADE, related_name='reversal_log')
    reversal_reference = models.CharField(max_length=100, unique=True)
    reversal_date = models.DateTimeField(default=timezone.now)
    reversal_reason = models.TextField()
    reversed_by = models.ForeignKey('people.Person', on_delete=models.SET_NULL, null=True, blank=True)
    journal_entry_reversed = models.BooleanField(default=False)
    reversal_amount = models.DecimalField(max_digits=12, decimal_places=2)
    approval_required = models.BooleanField(default=True)
    approved_by = models.ForeignKey('people.Person', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_reversals')
    approval_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Reversal: {self.original_payment.reference} - ${self.reversal_amount}"