from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from backend.apps.tenants.models import Tenant, School
from backend.apps.efbm.models import JournalEvent, JournalEntry
from backend.apps.efbm.services.accounting import (
    JournalPostingService, GeneralLedgerService, FinancialStatementService
)

class FinanceRelease2TestCase(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Accounting Tenant")
        self.school = School.objects.create(tenant=self.tenant, name="Imperial Academy of Commerce")
        self.client = APIClient()

    def test_journal_posting_and_trial_balance(self):
        # 1. Post Fee Revenue Journal (Debit Cash, Credit Tuition Revenue)
        post_res = JournalPostingService.post_journal_entry(
            school=self.school,
            event_type="fee_billing",
            debit_account="Cash at Bank",
            credit_account="Tuition Revenue",
            amount=5000.00
        )
        self.assertEqual(post_res["status"], "success")
        self.assertTrue(post_res["is_balanced"])

        # 2. Get Trial Balance
        tb = GeneralLedgerService.get_trial_balance(self.school)
        self.assertEqual(tb["total_debits"], 5000.00)
        self.assertEqual(tb["total_credits"], 5000.00)
        self.assertTrue(tb["is_balanced"])

        # 3. Financial Statements
        pl = FinancialStatementService.generate_profit_loss(self.school)
        self.assertEqual(pl["total_revenue"], 5000.00)
        self.assertEqual(pl["net_income"], 5000.00)

        bs = FinancialStatementService.generate_balance_sheet(self.school)
        self.assertEqual(bs["total_assets"], 5000.00)
        self.assertTrue(bs["is_balanced"])

    def test_accounting_api_endpoints(self):
        # 1. Journal Post API
        post_url = '/efbm/api/v1/journals/post/'
        payload = {
            "school_id": str(self.school.id),
            "event_type": "payroll_payout",
            "debit_account": "Payroll Expense",
            "credit_account": "Bank Account",
            "amount": 1200.00
        }
        resp = self.client.post(post_url, payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["status"], "success")

        # 2. Trial Balance API
        tb_url = f'/efbm/api/v1/trial-balance/?school_id={self.school.id}'
        tb_resp = self.client.get(tb_url)
        self.assertEqual(tb_resp.status_code, status.HTTP_200_OK)
        self.assertTrue(tb_resp.data["data"]["is_balanced"])
