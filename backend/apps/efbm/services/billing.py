import uuid
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from backend.apps.efbm.models import (
    Invoice, InvoiceItem, StudentWallet, WalletTransaction, Payment, FeeStructure
)
from backend.apps.core.services.notifications import UnifiedNotificationService

class BillingService:
    """
    Automated Fee Billing & Invoicing Engine (EFBM).
    """
    @classmethod
    @transaction.atomic
    def generate_invoice(cls, student, school, academic_year, amount_due, items_list=None):
        tenant = school.tenant
        invoice_number = f"INV-{timezone.now().strftime('%Y%m')}-{str(uuid.uuid4())[:6].upper()}"

        due_date = timezone.now().date() + timezone.timedelta(days=30)

        invoice = Invoice.objects.create(
            tenant=tenant,
            student=student,
            invoice_number=invoice_number,
            issue_date=timezone.now().date(),
            due_date=due_date,
            status='issued'
        )

        total_computed = Decimal('0.00')

        if items_list:
            for item in items_list:
                amt = Decimal(str(item.get('amount', 0.00)))
                fee_struct, _ = FeeStructure.objects.get_or_create(
                    school=school,
                    academic_year=academic_year,
                    tenant=tenant,
                    name=item.get('description', 'Tuition Fee'),
                    defaults={'amount': amt, 'category': item.get('category', 'tuition')}
                )
                InvoiceItem.objects.create(
                    tenant=tenant,
                    invoice=invoice,
                    fee_structure=fee_struct,
                    amount=amt
                )
                total_computed += amt

        # Send Billing Notification Alert
        UnifiedNotificationService.send_notification(
            recipient=student.person.first_name,
            title="Invoice Issued",
            message=f"New Invoice #{invoice.invoice_number} of ${total_computed or amount_due} issued.",
            channels=['in_app', 'email']
        )

        return {
            "status": "success",
            "invoice_id": str(invoice.id),
            "invoice_number": invoice.invoice_number,
            "amount_due": float(total_computed or amount_due)
        }


class WalletService:
    """
    Prepaid Student Wallet & Ledger Service (EFBM).
    """
    @classmethod
    @transaction.atomic
    def fund_wallet(cls, student, amount, reference=None):
        tenant = student.tenant
        ref = reference or f"DEP-{timezone.now().strftime('%Y%m%d%H%M%S')}"

        wallet, _ = StudentWallet.objects.get_or_create(
            student=student,
            tenant=tenant,
            defaults={'balance': Decimal('0.00')}
        )

        wallet.balance += Decimal(str(amount))
        wallet.save()

        tx = WalletTransaction.objects.create(
            tenant=tenant,
            wallet=wallet,
            transaction_type='credit',
            amount=Decimal(str(amount)),
            reference=ref,
            description=f"Wallet Deposit of ${amount}"
        )

        return {
            "status": "success",
            "student_number": student.student_number,
            "new_balance": float(wallet.balance),
            "transaction_ref": tx.reference
        }

    @classmethod
    @transaction.atomic
    def pay_invoice_from_wallet(cls, student, invoice):
        tenant = student.tenant
        wallet, _ = StudentWallet.objects.get_or_create(student=student, tenant=tenant, defaults={'balance': Decimal('0.00')})

        # Sum total items
        total_due = sum(item.amount for item in invoice.items.all()) or Decimal('100.00')

        if wallet.balance < total_due:
            return {
                "status": "error",
                "message": f"Insufficient wallet balance. Wallet: ${wallet.balance}, Due: ${total_due}"
            }

        # 1. Debit Wallet
        wallet.balance -= total_due
        wallet.save()

        tx_ref = f"WAL-PAY-{invoice.invoice_number}"
        WalletTransaction.objects.create(
            tenant=tenant,
            wallet=wallet,
            transaction_type='debit',
            amount=total_due,
            reference=tx_ref,
            description=f"Payment for Invoice #{invoice.invoice_number}"
        )

        # 2. Update Invoice
        invoice.status = 'paid'
        invoice.save()

        # 3. Create Payment Record
        payment_ref = f"PAY-{invoice.invoice_number}"
        payment = Payment.objects.create(
            tenant=tenant,
            invoice=invoice,
            amount=total_due,
            payment_method='wallet',
            reference=payment_ref
        )

        return {
            "status": "success",
            "invoice_number": invoice.invoice_number,
            "payment_ref": payment.reference,
            "receipt_number": f"RCT-{payment.reference}",
            "remaining_wallet_balance": float(wallet.balance)
        }
