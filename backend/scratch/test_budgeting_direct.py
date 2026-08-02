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
from backend.apps.academic.models import AcademicYear
from backend.apps.efbm.models import Budget, BudgetItem
from backend.apps.efbm.services import BudgetManagementService

def run_tests():
    print("--- Running Budget Management Direct Verification ---")

    tenant = Tenant.objects.first() or Tenant.objects.create(name="Budgeting Tenant Direct")
    school = School.objects.filter(tenant=tenant).first() or School.objects.create(tenant=tenant, name="Academy High")

    year = AcademicYear.objects.filter(tenant=tenant).first() or AcademicYear.objects.create(
        tenant=tenant,
        school=school,
        name="2026/2027",
        code="2026-2027-BDG",
        start_date=timezone.now().date(),
        end_date=(timezone.now() + timedelta(days=365)).date()
    )

    budget = Budget.objects.create(
        tenant=tenant,
        school=school,
        academic_year=year,
        name="FY 2026/2027 Operating Budget",
        total_allocated=Decimal("50000.00"),
        total_spent=Decimal("12500.00"),
        status="draft"
    )

    item1 = BudgetItem.objects.create(
        tenant=tenant,
        budget=budget,
        category_name="IT Hardware & Infrastructure",
        allocated_amount=Decimal("30000.00"),
        spent_amount=Decimal("10000.00")
    )
    item2 = BudgetItem.objects.create(
        tenant=tenant,
        budget=budget,
        category_name="Administrative Supplies",
        allocated_amount=Decimal("20000.00"),
        spent_amount=Decimal("2500.00")
    )

    # 1. Test Budget Approval Workflow
    approved_bdg = BudgetManagementService.approve_budget(budget_id=budget.id)
    assert approved_bdg.status == "approved", "Budget approval status transition failure!"
    print(f"[PASS] Budget Approval Verified. Status: {approved_bdg.status}")

    # 2. Test Budget vs. Actual Variance Report
    report = BudgetManagementService.get_budget_vs_actual_report(budget_id=budget.id)
    assert len(report['items']) == 2, "Budget vs actual item count mismatch!"
    assert report['total_variance'] == Decimal("37500.00"), f"Budget variance amount mismatch: {report['total_variance']}"
    assert report['consumption_pct'] == Decimal("25.00"), f"Consumption percentage mismatch: {report['consumption_pct']}"
    print(f"[PASS] Budget vs. Actual Variance Verified. Total Allocated: ${report['total_allocated']}, Total Spent: ${report['total_spent']}, Variance: ${report['total_variance']} (Consumption: {report['consumption_pct']}%)")

    # 3. Test Forecast Dashboard Metrics
    metrics = BudgetManagementService.get_budget_forecast_dashboard(tenant=tenant)
    assert metrics['total_allocated'] >= Decimal("50000.00"), "Forecast dashboard allocated metrics failure!"
    assert metrics['total_remaining'] >= Decimal("37500.00"), "Forecast dashboard remaining metrics failure!"
    print(f"[PASS] Forecast Dashboard Metrics Verified. Total Allocated: ${metrics['total_allocated']}, Remaining: ${metrics['total_remaining']}")

    print("--- ALL BUDGET MANAGEMENT VERIFICATION TESTS PASSED CLEANLY! ---")

if __name__ == "__main__":
    run_tests()
