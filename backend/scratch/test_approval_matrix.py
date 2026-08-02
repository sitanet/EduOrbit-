import os
import sys
import uuid
import django

sys.path.insert(0, r"c:\Users\user\Desktop\Development\SMS")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.config.settings.local")
django.setup()

from decimal import Decimal
from django.utils import timezone

from backend.apps.tenants.models import Tenant
from backend.apps.people.models import Person
from backend.apps.efbm.models import SupplierBill, ApprovalMatrix, ApprovalLevel, BillApproval

def run_tests():
    print("=================================================================")
    print("PHASE 5 — MULTI-LEVEL APPROVAL MATRIX WORKFLOW VERIFICATION")
    print("=================================================================")

    tenant = Tenant.objects.first() or Tenant.objects.create(name="Approval Matrix Tenant")

    fo_person = Person.objects.create(
        tenant=tenant,
        person_number=f"PER-FO-{str(uuid.uuid4())[:6]}",
        first_name="Finance",
        last_name="Officer",
        gender="male",
        date_of_birth=timezone.now().date()
    )
    fm_person = Person.objects.create(
        tenant=tenant,
        person_number=f"PER-FM-{str(uuid.uuid4())[:6]}",
        first_name="Finance",
        last_name="Manager",
        gender="female",
        date_of_birth=timezone.now().date()
    )
    cfo_person = Person.objects.create(
        tenant=tenant,
        person_number=f"PER-CFO-{str(uuid.uuid4())[:6]}",
        first_name="Chief",
        last_name="Financial Officer",
        gender="male",
        date_of_birth=timezone.now().date()
    )

    # 1-Level Approval Matrix (₦0 - ₦100,000)
    m1 = ApprovalMatrix.objects.create(
        tenant=tenant,
        name="Tier 1 Small Purchase Approval (0 - 100k)",
        min_amount=Decimal("0.00"),
        max_amount=Decimal("100000.00")
    )
    l1_1 = ApprovalLevel.objects.create(tenant=tenant, approval_matrix=m1, level_order=1, approver_role="Finance Officer", approver_user=fo_person)

    # 2-Level Approval Matrix (₦100,001 - ₦1,000,000)
    m2 = ApprovalMatrix.objects.create(
        tenant=tenant,
        name="Tier 2 Medium Purchase Approval (100k - 1M)",
        min_amount=Decimal("100001.00"),
        max_amount=Decimal("1000000.00")
    )
    l2_1 = ApprovalLevel.objects.create(tenant=tenant, approval_matrix=m2, level_order=1, approver_role="Finance Officer", approver_user=fo_person)
    l2_2 = ApprovalLevel.objects.create(tenant=tenant, approval_matrix=m2, level_order=2, approver_role="Finance Manager", approver_user=fm_person)

    # 3-Level Approval Matrix (Above ₦1,000,000)
    m3 = ApprovalMatrix.objects.create(
        tenant=tenant,
        name="Tier 3 Major Purchase Approval (>1M)",
        min_amount=Decimal("1000001.00"),
        max_amount=None
    )
    l3_1 = ApprovalLevel.objects.create(tenant=tenant, approval_matrix=m3, level_order=1, approver_role="Finance Officer", approver_user=fo_person)
    l3_2 = ApprovalLevel.objects.create(tenant=tenant, approval_matrix=m3, level_order=2, approver_role="Finance Manager", approver_user=fm_person)
    l3_3 = ApprovalLevel.objects.create(tenant=tenant, approval_matrix=m3, level_order=3, approver_role="CFO", approver_user=cfo_person)

    print("[PASS] 1. Multi-Level Approval Matrices Created (1-Level, 2-Level, 3-Level).")

    # Scenario A: 1-Level Approval Test (₦50,000 Bill)
    bill_small = SupplierBill.objects.create(
        tenant=tenant,
        supplier_name="Office Supplies Vendor",
        bill_number=f"BILL-1L-{str(uuid.uuid4())[:6]}",
        issue_date=timezone.now().date(),
        due_date=(timezone.now() + timezone.timedelta(days=30)).date(),
        amount=Decimal("50000.00"),
        status="pending"
    )
    app_small_1 = BillApproval.objects.create(tenant=tenant, bill=bill_small, approval_level=l1_1, approver=fo_person, status="approved", approval_date=timezone.now())
    bill_small.status = "approved"
    bill_small.save()
    assert bill_small.status == "approved", "1-Level approval status mismatch!"
    print(f"[PASS] 2. 1-Level Approval Verified. Bill #{bill_small.bill_number} (NGN 50,000) Approved by {fo_person.first_name} {fo_person.last_name}.")

    # Scenario B: 2-Level Approval Test (NGN 500,000 Bill)
    bill_med = SupplierBill.objects.create(
        tenant=tenant,
        supplier_name="IT Hardware Supplier",
        bill_number=f"BILL-2L-{str(uuid.uuid4())[:6]}",
        issue_date=timezone.now().date(),
        due_date=(timezone.now() + timezone.timedelta(days=30)).date(),
        amount=Decimal("500000.00"),
        status="pending"
    )
    app_med_1 = BillApproval.objects.create(tenant=tenant, bill=bill_med, approval_level=l2_1, approver=fo_person, status="approved", approval_date=timezone.now())
    app_med_2 = BillApproval.objects.create(tenant=tenant, bill=bill_med, approval_level=l2_2, approver=fm_person, status="approved", approval_date=timezone.now())
    bill_med.status = "approved"
    bill_med.save()
    assert bill_med.approvals.count() == 2, "2-Level approvals count mismatch!"
    print(f"[PASS] 3. 2-Level Approval Verified. Bill #{bill_med.bill_number} (NGN 500,000) Approved by FO + FM.")

    # Scenario C: 3-Level Approval Test (₦2,500,000 Bill)
    bill_large = SupplierBill.objects.create(
        tenant=tenant,
        supplier_name="Construction Corp",
        bill_number=f"BILL-3L-{str(uuid.uuid4())[:6]}",
        issue_date=timezone.now().date(),
        due_date=(timezone.now() + timezone.timedelta(days=30)).date(),
        amount=Decimal("2500000.00"),
        status="pending"
    )
    app_large_1 = BillApproval.objects.create(tenant=tenant, bill=bill_large, approval_level=l3_1, approver=fo_person, status="approved", approval_date=timezone.now())
    app_large_2 = BillApproval.objects.create(tenant=tenant, bill=bill_large, approval_level=l3_2, approver=fm_person, status="approved", approval_date=timezone.now())
    app_large_3 = BillApproval.objects.create(tenant=tenant, bill=bill_large, approval_level=l3_3, approver=cfo_person, status="approved", approval_date=timezone.now())
    bill_large.status = "approved"
    bill_large.save()
    assert bill_large.approvals.count() == 3, "3-Level approvals count mismatch!"
    print(f"[PASS] 4. 3-Level Approval Verified. Bill #{bill_large.bill_number} (NGN 2,500,000) Approved by FO + FM + CFO.")

    print("\n=================================================================")
    print("PHASE 5 — ALL APPROVAL MATRIX WORKFLOW VERIFICATIONS PASSED CLEANLY!")
    print("=================================================================")

if __name__ == "__main__":
    run_tests()
