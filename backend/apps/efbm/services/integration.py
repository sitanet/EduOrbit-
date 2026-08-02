from decimal import Decimal
from django.db import transaction
from django.utils import timezone

from backend.apps.efbm.models import JournalEvent, JournalEntry, LedgerPosting


class AutomaticAccountingIntegrationService:
    """
    Enterprise Automatic Accounting Integration Service for EduOrbit ERP.
    Handles double-entry general ledger postings across 11 core ERP domain modules:
    Admissions, School Fees, Hostel, Transport, Library, Clinic, Payroll, Inventory,
    Purchasing, Asset Disposal, and Refunds.
    All postings enforce @transaction.atomic, idempotency checks, and audit posting logs.
    """

    @classmethod
    @transaction.atomic
    def _create_balanced_journal(cls, tenant, event_type, reference_id, debit_account, credit_account, amount):
        """
        Internal engine creating double-entry debit & credit lines inside an atomic transaction.
        Enforces idempotency to prevent duplicate postings.
        """
        amount = Decimal(str(amount))
        unique_event_key = f"{event_type}_{reference_id}"

        # Idempotency check: prevent duplicate journal posting
        existing_event = JournalEvent.objects.filter(tenant=tenant, event_type=unique_event_key).first()
        if existing_event:
            return existing_event

        event = JournalEvent.objects.create(
            tenant=tenant,
            event_type=unique_event_key,
            timestamp=timezone.now()
        )

        debit_entry = JournalEntry.objects.create(
            tenant=tenant,
            event=event,
            account_name=debit_account,
            amount=amount,
            entry_type='debit'
        )

        credit_entry = JournalEntry.objects.create(
            tenant=tenant,
            event=event,
            account_name=credit_account,
            amount=amount,
            entry_type='credit'
        )

        # Audit ledger posting logs
        LedgerPosting.objects.create(tenant=tenant, entry=debit_entry, posting_date=timezone.now().date())
        LedgerPosting.objects.create(tenant=tenant, entry=credit_entry, posting_date=timezone.now().date())

        return event

    @classmethod
    def post_admissions_application_fee(cls, tenant, reference_id, amount):
        """1. Admissions Application Fee Posting (Dr: Cash, Cr: Other Educational Income)"""
        return cls._create_balanced_journal(tenant, 'admissions_fee', reference_id, 'Cash & Bank Accounts', 'Other Educational Income', amount)

    @classmethod
    def post_school_fee_billing(cls, tenant, reference_id, amount):
        """2. School Fee Billing Posting (Dr: Student Receivables, Cr: Tuition Revenue)"""
        return cls._create_balanced_journal(tenant, 'school_fee_billing', reference_id, 'Student Receivables', 'Tuition Revenue', amount)

    @classmethod
    def post_hostel_fee_billing(cls, tenant, reference_id, amount):
        """3. Hostel Fee Billing Posting (Dr: Student Receivables, Cr: Hostel Fee Revenue)"""
        return cls._create_balanced_journal(tenant, 'hostel_fee_billing', reference_id, 'Student Receivables', 'Hostel Fee Revenue', amount)

    @classmethod
    def post_transport_fee_billing(cls, tenant, reference_id, amount):
        """4. Transport Fee Billing Posting (Dr: Student Receivables, Cr: Transport Fee Revenue)"""
        return cls._create_balanced_journal(tenant, 'transport_fee_billing', reference_id, 'Student Receivables', 'Transport Fee Revenue', amount)

    @classmethod
    def post_library_fine_or_fee(cls, tenant, reference_id, amount):
        """5. Library Fine / Fee Posting (Dr: Cash, Cr: Other Educational Income)"""
        return cls._create_balanced_journal(tenant, 'library_fee', reference_id, 'Cash & Bank Accounts', 'Other Educational Income', amount)

    @classmethod
    def post_clinic_medical_fee(cls, tenant, reference_id, amount):
        """6. Clinic Medical Service Posting (Dr: Cash, Cr: Other Educational Income)"""
        return cls._create_balanced_journal(tenant, 'clinic_fee', reference_id, 'Cash & Bank Accounts', 'Other Educational Income', amount)

    @classmethod
    def post_payroll_disbursement(cls, tenant, reference_id, amount):
        """7. Payroll Disbursement Posting (Dr: Staff Salaries & Payroll, Cr: Cash)"""
        return cls._create_balanced_journal(tenant, 'payroll_disbursement', reference_id, 'Staff Salaries & Payroll', 'Cash & Bank Accounts', amount)

    @classmethod
    def post_inventory_purchase(cls, tenant, reference_id, amount):
        """8. Inventory Acquisition Posting (Dr: Inventory Assets, Cr: Accounts Payable)"""
        return cls._create_balanced_journal(tenant, 'inventory_purchase', reference_id, 'Inventory Assets', 'Accounts Payable', amount)

    @classmethod
    def post_purchasing_vendor_bill(cls, tenant, reference_id, amount):
        """9. Purchasing Vendor Bill Posting (Dr: Administrative Expenses, Cr: Accounts Payable)"""
        return cls._create_balanced_journal(tenant, 'purchasing_vendor_bill', reference_id, 'Administrative Expenses', 'Accounts Payable', amount)

    @classmethod
    def post_asset_disposal(cls, tenant, reference_id, amount):
        """10. Asset Disposal Posting (Dr: Cash, Cr: Equipment & Facilities)"""
        return cls._create_balanced_journal(tenant, 'asset_disposal', reference_id, 'Cash & Bank Accounts', 'Equipment & Facilities', amount)

    @classmethod
    def post_student_fee_refund(cls, tenant, reference_id, amount):
        """11. Student Fee Refund Posting (Dr: Tuition Revenue, Cr: Cash & Bank Accounts)"""
        return cls._create_balanced_journal(tenant, 'student_fee_refund', reference_id, 'Tuition Revenue', 'Cash & Bank Accounts', amount)

    @classmethod
    def post_supplier_credit_note(cls, tenant, reference_id, amount):
        """12. Supplier Credit Note Posting (Dr: Accounts Payable, Cr: Administrative Expenses)"""
        return cls._create_balanced_journal(tenant, 'supplier_credit_note', reference_id, 'Accounts Payable', 'Administrative Expenses', amount)

    @classmethod
    def post_supplier_debit_note(cls, tenant, reference_id, amount):
        """13. Supplier Debit Note Posting (Dr: Administrative Expenses, Cr: Accounts Payable)"""
        return cls._create_balanced_journal(tenant, 'supplier_debit_note', reference_id, 'Administrative Expenses', 'Accounts Payable', amount)

    @classmethod
    def post_supplier_payment(cls, tenant, reference_id, amount):
        """14. Supplier Payment Posting (Dr: Accounts Payable, Cr: Cash & Bank Accounts)"""
        return cls._create_balanced_journal(tenant, 'supplier_payment', reference_id, 'Accounts Payable', 'Cash & Bank Accounts', amount)

    @classmethod
    def post_withholding_tax(cls, tenant, reference_id, amount):
        """15. Withholding Tax Posting (Dr: Withholding Tax Payable, Cr: Cash & Bank Accounts)"""
        return cls._create_balanced_journal(tenant, 'withholding_tax', reference_id, 'Withholding Tax Payable', 'Cash & Bank Accounts', amount)

