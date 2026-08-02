import os
import sys
import django

sys.path.insert(0, r"c:\Users\user\Desktop\Development\SMS")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.config.settings.local")
django.setup()

from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

from backend.apps.tenants.models import Tenant, School
from backend.apps.people.models import Person, StudentProfile
from backend.apps.efbm.models import Invoice, InvoiceItem, Payment, FeeStructure
from backend.apps.academic.models import AcademicYear
from backend.apps.efbm.services import AccountsReceivableService

def run_tests():
    print("--- Running Accounts Receivable Direct Verification ---")

    tenant = Tenant.objects.first() or Tenant.objects.create(name="Receivables Tenant Direct")
    school = School.objects.filter(tenant=tenant).first() or School.objects.create(tenant=tenant, name="Academy High")
    
    person = Person.objects.create(
        tenant=tenant,
        person_number="PERS-REC-001",
        date_of_birth=timezone.now().date(),
        first_name="Alice",
        last_name="Smith"
    )
    student = StudentProfile.objects.create(
        tenant=tenant,
        person=person,
        current_school=school,
        student_number="STD-REC-001"
    )

    year = AcademicYear.objects.filter(tenant=tenant).first() or AcademicYear.objects.create(
        tenant=tenant,
        school=school,
        name="2026/2027",
        code="2026-2027-REC",
        start_date=timezone.now().date(),
        end_date=(timezone.now() + timedelta(days=365)).date()
    )

    fee_struct = FeeStructure.objects.create(
        tenant=tenant,
        school=school,
        academic_year=year,
        name="Tuition Fee Q1",
        amount=Decimal("1500.00")
    )

    invoice = Invoice.objects.create(
        tenant=tenant,
        student=student,
        invoice_number="INV-REC-1001",
        issue_date=timezone.now().date(),
        due_date=(timezone.now() - timedelta(days=45)).date(),  # Overdue by 45 days -> 31-60 bucket
        status="issued"
    )
    InvoiceItem.objects.create(
        tenant=tenant,
        invoice=invoice,
        fee_structure=fee_struct,
        amount=Decimal("1500.00")
    )

    # 1. Test Student Statement
    stmt = AccountsReceivableService.get_student_statement(student_id=student.id)
    assert len(stmt['lines']) >= 1, "Student statement lines count failure!"
    assert stmt['total_billed'] >= Decimal("1500.00"), "Student statement total billed mismatch!"
    print(f"[PASS] Student Statement Verified. Billed: ${stmt['total_billed']}, Ending Balance: ${stmt['ending_balance']}")

    # 2. Test Outstanding Invoices
    outstandings = AccountsReceivableService.get_outstanding_invoices(tenant=tenant)
    assert len(outstandings) >= 1, "Outstanding invoices count failure!"
    print(f"[PASS] Outstanding Invoices Verified. Count: {len(outstandings)}")

    # 3. Test Invoice Aging Analysis
    aging = AccountsReceivableService.get_invoice_aging_report(tenant=tenant)
    assert aging['bucket_31_60'] >= Decimal("1500.00"), "Aging bucket (31-60 days) classification failure!"
    print(f"[PASS] Invoice Aging Analysis Verified. 31-60 Days Bucket: ${aging['bucket_31_60']}")

    # 4. Test Receivables Dashboard Metrics
    metrics = AccountsReceivableService.get_receivables_dashboard_widgets(tenant=tenant)
    assert metrics['total_receivables'] >= Decimal("1500.00"), "Receivables dashboard metrics failure!"
    print(f"[PASS] Receivables Dashboard Metrics Verified. Total Receivables: ${metrics['total_receivables']}")

    print("--- ALL ACCOUNTS RECEIVABLE VERIFICATION TESTS PASSED CLEANLY! ---")

if __name__ == "__main__":
    run_tests()
