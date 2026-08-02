from decimal import Decimal
from django.test import TestCase
from django.utils import timezone

from backend.apps.tenants.models import Tenant, School
from backend.apps.efbm.models import Invoice, Payment, JournalEvent, JournalEntry
from backend.apps.efbm.services import FinancialReportingService


class FinancialReportingEngineTests(TestCase):
    """
    Unit test suite for Trial Balance, Balance Sheet, and Income Statement generation.
    """

    def setUp(self):
        self.tenant = Tenant.objects.create(name="Finance Test Tenant")
        self.school = School.objects.create(tenant=self.tenant, name="Capital Academy")
        
        # Create a double-entry Journal Event
        self.event = JournalEvent.objects.create(
            tenant=self.tenant,
            event_type="fee_billing",
            timestamp=timezone.now()
        )
        self.debit_entry = JournalEntry.objects.create(
            tenant=self.tenant,
            event=self.event,
            account_name="Student Receivables",
            amount=Decimal("5000.00"),
            entry_type="debit"
        )
        self.credit_entry = JournalEntry.objects.create(
            tenant=self.tenant,
            event=self.event,
            account_name="Tuition Revenue",
            amount=Decimal("5000.00"),
            entry_type="credit"
        )

    def test_trial_balance_calculation_and_balancing(self):
        tb = FinancialReportingService.get_trial_balance(tenant=self.tenant)
        self.assertTrue(tb['is_balanced'])
        self.assertEqual(tb['total_debit'], Decimal("5000.00"))
        self.assertEqual(tb['total_credit'], Decimal("5000.00"))

    def test_income_statement_calculation(self):
        pnl = FinancialReportingService.get_income_statement(tenant=self.tenant)
        self.assertEqual(pnl['revenue'], Decimal("5000.00"))
        self.assertEqual(pnl['net_profit'], Decimal("5000.00"))

    def test_balance_sheet_calculation_and_equation(self):
        bs = FinancialReportingService.get_balance_sheet(tenant=self.tenant)
        self.assertTrue(bs['is_balanced'])
        self.assertEqual(bs['total_assets'], Decimal("5000.00"))
        self.assertEqual(bs['total_liabilities_equity'], Decimal("5000.00"))
