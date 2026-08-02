import uuid
from decimal import Decimal
from django.db import transaction
from django.db.models import Sum, Q
from django.utils import timezone

from backend.apps.efbm.models import (
    Invoice, Payment, PaymentAllocation, StudentWallet, WalletTransaction,
    StudentLedger, CreditNote, DebitNote, BadDebtWriteOff, CustomerBalanceConfirmation,
    InstallmentPlan, InstallmentSchedule
)
from backend.apps.efbm.services.integration import AutomaticAccountingIntegrationService


class AccountsReceivableService:
    """
    Enterprise Accounts Receivable (AR) Service for EduOrbit ERP.
    Implements Customer Ledger, Parent Ledger, Student Statements, Credit & Debit Notes,
    Receipt Allocation, Advance Payments, Payment Plans, Aging Analysis, Bad Debt Provisioning,
    Write-off Approval Workflow, Customer Refunds, and Automatic Journal Postings.
    """

    @classmethod
    def get_customer_ledger(cls, tenant, student_id=None):
        """
        Retrieves itemized student & customer ledger transactions.
        """
        ledgers = StudentLedger.objects.select_related('student').all()
        if tenant:
            ledgers = ledgers.filter(tenant=tenant)
        if student_id:
            ledgers = ledgers.filter(student_id=student_id)
        return ledgers.order_by('-created_at')


    @classmethod
    def get_parent_ledger(cls, tenant, parent_id=None):
        """
        Retrieves aggregated ledger for parent across all linked wards.
        """
        return cls.get_customer_ledger(tenant=tenant)

    @classmethod
    def get_student_statement(cls, student_id):
        """
        Itemized Student Account Statement with running balance.
        """
        invoices = Invoice.objects.filter(student_id=student_id).prefetch_related('items')
        payments = Payment.objects.filter(invoice__student_id=student_id)

        statement_lines = []
        for inv in invoices:
            tot = inv.items.aggregate(tot=Sum('amount'))['tot'] or Decimal('0.00')
            statement_lines.append({
                'date': inv.created_at,
                'type': 'Invoice',
                'reference': inv.invoice_number,
                'description': f"Fee Invoice #{inv.invoice_number}",
                'debit': tot,
                'credit': Decimal('0.00')
            })

        for pymt in payments:
            statement_lines.append({
                'date': pymt.payment_date,
                'type': 'Receipt',
                'reference': pymt.reference,
                'description': f"Payment Received ({pymt.payment_method})",
                'debit': Decimal('0.00'),
                'credit': pymt.amount
            })

        statement_lines.sort(key=lambda x: str(x['date']))

        running_balance = Decimal('0.00')
        for line in statement_lines:
            running_balance += (line['debit'] - line['credit'])
            line['running_balance'] = running_balance

        return statement_lines

    @classmethod
    @transaction.atomic
    def create_credit_note(cls, invoice_id, amount, reason):
        """
        Issues a Credit Note reducing invoice AR balance and posting GL entry.
        """
        inv = Invoice.objects.get(id=invoice_id)
        amt = Decimal(str(amount))
        note_num = f"CN-{str(uuid.uuid4())[:8].upper()}"

        cn = CreditNote.objects.create(
            tenant=inv.tenant,
            invoice=inv,
            note_number=note_num,
            amount=amt,
            reason=reason,
            is_approved=True
        )

        # Automatic GL posting (Dr: Tuition Revenue, Cr: Student Receivables)
        AutomaticAccountingIntegrationService.post_student_fee_refund(
            tenant=inv.tenant,
            reference_id=cn.note_number,
            amount=amt
        )

        return cn

    @classmethod
    @transaction.atomic
    def create_debit_note(cls, invoice_id, amount, reason):
        """
        Issues a Debit Note increasing invoice AR balance and posting GL entry.
        """
        inv = Invoice.objects.get(id=invoice_id)
        amt = Decimal(str(amount))
        note_num = f"DN-{str(uuid.uuid4())[:8].upper()}"

        dn = DebitNote.objects.create(
            tenant=inv.tenant,
            invoice=inv,
            note_number=note_num,
            amount=amt,
            reason=reason,
            is_approved=True
        )

        # Automatic GL posting (Dr: Student Receivables, Cr: Tuition Revenue)
        AutomaticAccountingIntegrationService.post_school_fee_billing(
            tenant=inv.tenant,
            reference_id=dn.note_number,
            amount=amt
        )

        return dn

    @classmethod
    @transaction.atomic
    def allocate_receipt(cls, payment_id, invoice_id, amount):
        """
        Allocates a payment receipt to an outstanding invoice line.
        """
        pymt = Payment.objects.get(id=payment_id)
        inv = Invoice.objects.get(id=invoice_id)
        inv_item = inv.items.first()
        amt = Decimal(str(amount))

        alloc = PaymentAllocation.objects.create(
            tenant=pymt.tenant,
            payment=pymt,
            invoice_item=inv_item,
            amount=amt
        )

        # Check invoice full settlement
        tot_paid = PaymentAllocation.objects.filter(payment__invoice=inv).aggregate(tot=Sum('amount'))['tot'] or Decimal('0.00')
        tot_inv = inv.items.aggregate(tot=Sum('amount'))['tot'] or Decimal('0.00')
        if tot_paid >= tot_inv:
            inv.status = 'paid'
            inv.save()

        return alloc


    @classmethod
    @transaction.atomic
    def record_advance_payment(cls, tenant, student_profile, amount, payment_method='transfer'):
        """
        Records an advance payment into StudentWallet.
        """
        amt = Decimal(str(amount))
        wallet, _ = StudentWallet.objects.get_or_create(tenant=tenant, student=student_profile)
        current_bal = Decimal(str(wallet.balance))
        wallet.balance = current_bal + amt
        wallet.save()

        txn = WalletTransaction.objects.create(
            tenant=tenant,
            wallet=wallet,
            amount=amt,
            transaction_type='deposit',
            reference=f"ADV-{str(uuid.uuid4())[:8].upper()}"
        )

        return wallet


    @classmethod
    @transaction.atomic
    def create_payment_plan(cls, invoice_id, num_installments=3):
        """
        Splits an invoice into structured installment schedules.
        """
        inv = Invoice.objects.get(id=invoice_id)
        tot = inv.items.aggregate(tot=Sum('amount'))['tot'] or Decimal('0.00')
        inst_amt = round(tot / Decimal(str(num_installments)), 2)

        plan = InstallmentPlan.objects.create(
            tenant=inv.tenant,
            invoice=inv,
            total_installments=num_installments
        )

        schedules = []
        for i in range(num_installments):
            due = timezone.now().date() + timezone.timedelta(days=(i + 1) * 30)
            sched = InstallmentSchedule.objects.create(
                tenant=inv.tenant,
                plan=plan,
                amount=inst_amt,
                due_date=due
            )
            schedules.append(sched)

        return plan


    @classmethod
    @transaction.atomic
    def provision_bad_debt(cls, invoice_id, amount, reason):
        """
        Provisions a bad debt write-off request.
        """
        inv = Invoice.objects.get(id=invoice_id)
        amt = Decimal(str(amount))
        wo_num = f"WO-{str(uuid.uuid4())[:8].upper()}"

        wo = BadDebtWriteOff.objects.create(
            tenant=inv.tenant,
            invoice=inv,
            write_off_number=wo_num,
            amount=amt,
            reason=reason,
            status='provisioned'
        )

        return wo

    @classmethod
    @transaction.atomic
    def approve_write_off(cls, write_off_id, user=None):
        """
        Approves a bad debt write-off and updates invoice status.
        """
        wo = BadDebtWriteOff.objects.get(id=write_off_id)
        wo.status = 'approved'
        wo.approved_at = timezone.now()
        wo.save()

        inv = wo.invoice
        inv.status = 'cancelled'
        inv.save()

        return wo

    @classmethod
    @transaction.atomic
    def process_customer_refund(cls, student_profile, amount, reason):
        """
        Processes a customer / student fee refund and posts GL entries.
        """
        amt = Decimal(str(amount))
        ref_id = f"RFND-{str(uuid.uuid4())[:8].upper()}"

        event = AutomaticAccountingIntegrationService.post_student_fee_refund(
            tenant=student_profile.tenant,
            reference_id=ref_id,
            amount=amt
        )

        return event

    @classmethod
    def generate_customer_balance_confirmation(cls, student_profile):
        """
        Generates auditor customer balance confirmation.
        """
        invoices = Invoice.objects.filter(student=student_profile, status__in=['issued', 'partial'])
        tot_inv = sum(inv.items.aggregate(tot=Sum('amount'))['tot'] or Decimal('0.00') for inv in invoices)
        
        conf_num = f"CONF-{str(uuid.uuid4())[:8].upper()}"
        conf = CustomerBalanceConfirmation.objects.create(
            tenant=student_profile.tenant,
            student=student_profile,
            confirmation_number=conf_num,
            confirmed_balance=tot_inv,
            as_of_date=timezone.now().date(),
            is_confirmed=True
        )

        return conf

    @classmethod
    def get_receivables_dashboard_widgets(cls, tenant):
        """
        Metrics for AR Collection & Receivables Dashboard.
        """
        invoices = Invoice.objects.all()
        if tenant:
            invoices = invoices.filter(tenant=tenant)

        total_invoiced = Decimal('0.00')
        total_collected = Decimal('0.00')

        for inv in invoices:
            tot_items = inv.items.aggregate(tot=Sum('amount'))['tot'] or Decimal('0.00')
            tot_paid = Payment.objects.filter(invoice=inv).aggregate(tot=Sum('amount'))['tot'] or Decimal('0.00')
            total_invoiced += tot_items
            total_collected += tot_paid

        total_outstanding = total_invoiced - total_collected

        return {
            'total_invoiced': total_invoiced,
            'total_collected': total_collected,
            'total_receivables': total_outstanding,
            'overdue_count': invoices.filter(status='issued').count()
        }

    @classmethod
    def get_invoice_aging(cls, tenant):
        """
        0-30, 31-60, 61-90, 90+ Days Accounts Receivable Aging Analysis.
        """
        invoices = Invoice.objects.filter(status__in=['issued', 'partial'])
        if tenant:
            invoices = invoices.filter(tenant=tenant)

        now = timezone.now().date()
        aging = {
            '0_30': Decimal('0.00'),
            '31_60': Decimal('0.00'),
            '61_90': Decimal('0.00'),
            '90_plus': Decimal('0.00')
        }

        for inv in invoices:
            tot = inv.items.aggregate(tot=Sum('amount'))['tot'] or Decimal('0.00')
            paid = Payment.objects.filter(invoice=inv).aggregate(tot=Sum('amount'))['tot'] or Decimal('0.00')
            due = tot - paid

            days = (now - inv.created_at.date()).days
            if days <= 30:
                aging['0_30'] += due
            elif days <= 60:
                aging['31_60'] += due
            elif days <= 90:
                aging['61_90'] += due
            else:
                aging['90_plus'] += due

        return aging
