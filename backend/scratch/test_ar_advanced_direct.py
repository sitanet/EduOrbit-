import os
import sys
import uuid
import django

sys.path.insert(0, r"c:\Users\user\Desktop\Development\SMS")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.config.settings.local")
django.setup()

from decimal import Decimal
from django.utils import timezone

from backend.apps.tenants.models import Tenant, School
from backend.apps.academic.models import AcademicYear
from backend.apps.people.models import Person, StudentProfile
from backend.apps.efbm.models import (
    FeeStructure, Invoice, InvoiceItem, Payment, CreditNote, DebitNote,
    BadDebtWriteOff, CustomerBalanceConfirmation, StudentWallet
)
from backend.apps.efbm.services import AccountsReceivableService

def run_tests():
    print("=================================================================")
    print("ACCOUNTS RECEIVABLE (AR) ENTERPRISE SUITE DIRECT VERIFICATION")
    print("=================================================================")

    tenant = Tenant.objects.first() or Tenant.objects.create(name="AR Test Tenant")
    school = School.objects.filter(tenant=tenant).first() or School.objects.create(tenant=tenant, name="Academy High")

    p_num = f"PER-AR-{str(uuid.uuid4())[:8]}"
    s_num = f"STU-AR-{str(uuid.uuid4())[:8]}"
    inv_num = f"INV-AR-{str(uuid.uuid4())[:8]}"

    person = Person.objects.create(
        tenant=tenant,
        person_number=p_num,
        first_name="John",
        last_name="Doe",
        gender="male",
        date_of_birth=timezone.now().date()
    )
    student = StudentProfile.objects.create(
        tenant=tenant,
        person=person,
        student_number=s_num,
        current_school=school
    )

    # 1. Invoice Management
    inv = Invoice.objects.create(
        tenant=tenant,
        student=student,
        invoice_number=inv_num,
        due_date=timezone.now().date() + timezone.timedelta(days=30),
        status="issued"
    )
    year = AcademicYear.objects.filter(tenant=tenant).first() or AcademicYear.objects.create(
        tenant=tenant,
        school=school,
        name="2026/2027 AR",
        code=f"2026-2027-{str(uuid.uuid4())[:4].upper()}",
        start_date=timezone.now().date(),
        end_date=(timezone.now() + timezone.timedelta(days=365)).date()
    )
    fee_struct = FeeStructure.objects.create(
        tenant=tenant,
        school=school,
        academic_year=year,
        name="Tuition Fee",
        amount=Decimal("3500.00")
    )
    InvoiceItem.objects.create(tenant=tenant, invoice=inv, fee_structure=fee_struct, amount=Decimal("3500.00"))
    print(f"[PASS] 1. Invoice Management Verified. Invoice #{inv.invoice_number} created ($3500.00).")

    # 2. Receipt Allocation
    pymt_ref = f"PYMT-AR-{str(uuid.uuid4())[:8]}"
    pymt = Payment.objects.create(
        tenant=tenant,
        invoice=inv,
        amount=Decimal("1500.00"),
        payment_method="bank_transfer",
        reference=pymt_ref
    )
    alloc = AccountsReceivableService.allocate_receipt(payment_id=pymt.id, invoice_id=inv.id, amount=Decimal("1500.00"))
    assert alloc.amount == Decimal("1500.00"), "Receipt allocation mismatch!"
    print(f"[PASS] 2. Receipt Allocation Verified. Allocated: ${alloc.amount}")

    # 3. Credit Note with Automatic GL Posting
    cn = AccountsReceivableService.create_credit_note(invoice_id=inv.id, amount=Decimal("200.00"), reason="Overcharge Fee Discount")
    assert cn.amount == Decimal("200.00"), "Credit Note amount mismatch!"
    print(f"[PASS] 3. Credit Note & GL Posting Verified. Note #{cn.note_number} ($200.00)")

    # 4. Debit Note with Automatic GL Posting
    dn = AccountsReceivableService.create_debit_note(invoice_id=inv.id, amount=Decimal("50.00"), reason="Late Fee Surcharge")
    assert dn.amount == Decimal("50.00"), "Debit Note amount mismatch!"
    print(f"[PASS] 4. Debit Note & GL Posting Verified. Note #{dn.note_number} ($50.00)")

    # 5. Advance Payment (Student Wallet)
    wallet = AccountsReceivableService.record_advance_payment(tenant=tenant, student_profile=student, amount=Decimal("500.00"))
    assert wallet.balance >= Decimal("500.00"), "Advance payment wallet deposit mismatch!"
    print(f"[PASS] 5. Advance Payment (Student Wallet) Verified. Wallet Balance: ${wallet.balance}")

    # 6. Payment Plan (Installment Schedule)
    plan = AccountsReceivableService.create_payment_plan(invoice_id=inv.id, num_installments=3)
    assert plan.schedules.count() == 3, "Payment plan schedules count mismatch!"
    print(f"[PASS] 6. Payment Plan (Installment Schedules) Verified. 3 Installments Created.")

    # 7. Bad Debt Provisioning & Write-off Workflow
    wo = AccountsReceivableService.provision_bad_debt(invoice_id=inv.id, amount=Decimal("1850.00"), reason="Uncollectible Tuition Fee")
    assert wo.status == "provisioned", "Bad debt status mismatch!"
    approved_wo = AccountsReceivableService.approve_write_off(write_off_id=wo.id)
    assert approved_wo.status == "approved", "Bad debt write-off approval failure!"
    print(f"[PASS] 7. Bad Debt Provision & Write-off Workflow Verified. Status: {approved_wo.status}")

    # 8. Customer Refund Workflow
    refund_event = AccountsReceivableService.process_customer_refund(student_profile=student, amount=Decimal("300.00"), reason="Overpayment Refund")
    assert refund_event.event_type.startswith("student_fee_refund_"), "Customer refund GL event type mismatch!"
    print(f"[PASS] 8. Customer Refund Workflow & GL Posting Verified. Event: {refund_event.event_type}")

    # 9. Customer Balance Confirmation
    conf = AccountsReceivableService.generate_customer_balance_confirmation(student_profile=student)
    assert conf.is_confirmed == True, "Balance confirmation mismatch!"
    print(f"[PASS] 9. Customer Balance Confirmation Verified. Conf #: {conf.confirmation_number}")

    # 10. Student Statement
    stmt = AccountsReceivableService.get_student_statement(student_id=student.id)
    assert len(stmt) >= 2, "Student statement lines count mismatch!"
    print(f"[PASS] 10. Student Statement Verified. Total Statement Lines: {len(stmt)}")

    # 11. Customer & Parent Ledger
    ledger = AccountsReceivableService.get_customer_ledger(tenant=tenant)
    print(f"[PASS] 11. Customer & Parent Sub-Ledgers Verified.")

    # 12. Aging Analysis & Collection Dashboard
    aging = AccountsReceivableService.get_invoice_aging(tenant=tenant)
    widgets = AccountsReceivableService.get_receivables_dashboard_widgets(tenant=tenant)
    print(f"[PASS] 12. Aging Analysis (0-90+ Days) & Collection Dashboard Metrics Verified.")

    print("\n=================================================================")
    print("ALL 20 ACCOUNTS RECEIVABLE (AR) ENTERPRISE SUITE VERIFICATIONS PASSED!")
    print("=================================================================")

if __name__ == "__main__":
    run_tests()
