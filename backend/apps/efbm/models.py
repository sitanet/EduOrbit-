import uuid
from django.db import models
from django.utils import timezone
from backend.apps.core.models import TenantBaseModel, PlatformBaseModel

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
    Pre-paid funds account held by a Parent.
    """
    parent = models.ForeignKey('people.Person', on_delete=models.CASCADE, related_name='wallets')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Wallet: {self.parent.last_name} ({self.balance})"


class WalletTransaction(TenantBaseModel):
    wallet = models.ForeignKey(StudentWallet, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(max_length=20)  # credit, debit
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
