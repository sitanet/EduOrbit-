from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from backend.apps.tenants.models import Tenant, School
from backend.apps.academic.models import AcademicYear
from backend.apps.efbm.models import Budget, BudgetItem
from backend.apps.efbm.services.budgeting import BudgetService, BudgetControlService

class BudgetRelease5TestCase(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Budget Tenant")
        self.school = School.objects.create(tenant=self.tenant, name="Royal Governance School")
        self.year = AcademicYear.objects.create(
            tenant=self.tenant, school=self.school, name="2026/2027", code="2026-2027",
            start_date="2026-09-01", end_date="2027-07-15"
        )
        self.client = APIClient()

    def test_budget_creation_approval_and_control(self):
        # 1. Create Annual Budget
        b_res = BudgetService.create_budget(
            school=self.school,
            academic_year=self.year,
            name="2026/2027 Operating Budget",
            items_list=[
                {"category_name": "ICT Hardware", "allocated_amount": 10000.00},
                {"category_name": "Operating Supplies", "allocated_amount": 5000.00}
            ]
        )
        self.assertEqual(b_res["status"], "success")
        self.assertEqual(b_res["total_allocated"], 15000.00)
        budget = Budget.objects.get(id=b_res["budget_id"])

        # 2. Approve Budget
        app_res = BudgetService.approve_budget(budget=budget)
        self.assertEqual(app_res["status"], "success")
        self.assertEqual(app_res["status_name"], "approved")

        # 3. Reserve Commitment (PO Reservation)
        item = budget.items.get(category_name="ICT Hardware")
        res_res = BudgetControlService.reserve_commitment(budget_item=item, amount=3000.00)
        self.assertEqual(res_res["status"], "success")
        self.assertEqual(res_res["remaining_available"], 7000.00)

        # 4. Hard Budget Stop Check (Over-budget prevention)
        over_res = BudgetControlService.reserve_commitment(budget_item=item, amount=8000.00)
        self.assertEqual(over_res["status"], "error")
        self.assertTrue("Hard Budget Stop" in over_res["message"])

        # 5. Record Actual Expense
        exp_res = BudgetControlService.record_actual_expense(budget_item=item, amount=3000.00)
        self.assertEqual(exp_res["status"], "success")

        # 6. Utilization Report
        util = BudgetControlService.get_budget_utilization(budget=budget)
        self.assertEqual(util["total_spent"], 3000.00)
        self.assertEqual(util["utilization_percentage"], 20.0)

    def test_budget_api_endpoints(self):
        # 1. Create Budget API
        create_url = '/efbm/api/v1/budgets/'
        payload = {
            "school_id": str(self.school.id),
            "academic_year_id": str(self.year.id),
            "name": "Library Expansion Budget",
            "items": [{"category_name": "Books & Digital Media", "allocated_amount": 8000.00}]
        }
        resp = self.client.post(create_url, payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        budget_id = resp.data["data"]["budget_id"]

        # 2. Approve Budget API
        app_url = '/efbm/api/v1/budgets/approve/'
        app_resp = self.client.post(app_url, {"budget_id": budget_id}, format='json')
        self.assertEqual(app_resp.status_code, status.HTTP_200_OK)

        # 3. Budget Utilization API
        util_url = f'/efbm/api/v1/budget-utilization/?budget_id={budget_id}'
        util_resp = self.client.get(util_url)
        self.assertEqual(util_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(util_resp.data["data"]["total_allocated"], 8000.00)
