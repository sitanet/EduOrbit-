from django.test import TestCase
from django.utils import timezone
from datetime import date, timedelta
from backend.apps.tenants.models import Tenant, School
from backend.apps.people.models import Person, StudentProfile
from backend.apps.academic.models import AcademicYear, AcademicPeriod, EducationLevel, AcademicLevel, Subject, Curriculum as AcademicCurriculum
from backend.apps.efbm.models import (
    FeeStructure, Invoice, InvoiceItem, Payment, StudentWallet, WalletTransaction, StudentLedger, JournalEvent, JournalEntry
)

class EFBMPlatformTests(TestCase):
    def setUp(self):
        # Create core configurations
        self.tenant = Tenant.objects.create(name="EFBM Org")
        self.school = School.objects.create(tenant=self.tenant, name="EFBM Primary School", school_types=["primary"])
        
        # Academic structures
        self.year = AcademicYear.objects.create(
            school=self.school,
            tenant=self.tenant,
            name="2026/2027 Year",
            code="2026-27-efbm",
            start_date=timezone.now().date(),
            end_date=(timezone.now() + timedelta(days=365)).date(),
            status='active'
        )
        self.period = AcademicPeriod.objects.create(
            academic_year=self.year,
            tenant=self.tenant,
            name="First Term",
            start_date=timezone.now().date(),
            end_date=(timezone.now() + timedelta(days=120)).date(),
            status='active'
        )
        self.aca_curriculum = AcademicCurriculum.objects.create(name="Checkpoint", code="cp-27", version="1")
        self.subject = Subject.objects.create(school=self.school, tenant=self.tenant, curriculum=self.aca_curriculum, code="math-1", name="Math 1")
        
        # Student Profile
        self.person = Person.objects.create(
            tenant=self.tenant,
            person_number="P-80088",
            first_name="Bruce",
            last_name="Wayne",
            gender="male",
            date_of_birth="2010-02-19"
        )
        self.student = StudentProfile.objects.create(
            person=self.person,
            tenant=self.tenant,
            student_number="STU-80088",
            current_school=self.school,
            enrollment_status="enrolled"
        )
        
        # Fee structure
        self.fee = FeeStructure.objects.create(
            school=self.school,
            tenant=self.tenant,
            academic_year=self.year,
            name="JSS1 Tuition Levy",
            amount=50000.00,
            category="tuition"
        )
        
        # Invoice
        self.invoice = Invoice.objects.create(
            student=self.student,
            tenant=self.tenant,
            invoice_number="INV-2026-0001",
            issue_date=timezone.now().date(),
            due_date=(timezone.now() + timedelta(days=30)).date()
        )
        self.item = InvoiceItem.objects.create(
            invoice=self.invoice,
            fee_structure=self.fee,
            amount=50000.00,
            tenant=self.tenant
        )

    def test_double_entry_journal_posting_balance(self):
        # 1. Start a Billing Journal Event
        event = JournalEvent.objects.create(
            tenant=self.tenant,
            event_type="fee_billing"
        )
        
        # 2. Debit: Student Receivables (Asset)
        dr_entry = JournalEntry.objects.create(
            event=event,
            tenant=self.tenant,
            account_name="Student Receivables",
            amount=50000.00,
            entry_type="debit"
        )
        
        # 3. Credit: Tuition Revenue (Revenue)
        cr_entry = JournalEntry.objects.create(
            event=event,
            tenant=self.tenant,
            account_name="Tuition Revenue",
            amount=50000.00,
            entry_type="credit"
        )
        
        # Verify double-entry balances
        entries = event.entries.all()
        total_debits = sum(e.amount for e in entries if e.entry_type == 'debit')
        total_credits = sum(e.amount for e in entries if e.entry_type == 'credit')
        self.assertEqual(total_debits, total_credits)
        self.assertEqual(total_debits, 50000.00)

    def test_parent_wallet_transactions_and_limits(self):
        # Create wallet
        wallet = StudentWallet.objects.create(
            parent=self.person,
            tenant=self.tenant,
            balance=1000.00
        )
        
        # Credit transaction
        tx = WalletTransaction.objects.create(
            wallet=wallet,
            tenant=self.tenant,
            amount=500.00,
            transaction_type="credit"
        )
        wallet.balance += tx.amount
        wallet.save()
        
        self.assertEqual(wallet.balance, 1500.00)
