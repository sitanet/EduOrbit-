from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from backend.apps.tenants.models import Tenant, School
from backend.apps.people.models import Person, StudentProfile
from backend.apps.academic.models import AcademicYear
from backend.apps.efbm.models import Invoice, StudentWallet, Payment
from backend.apps.efbm.services.billing import BillingService, WalletService

class FinancePhase1TestCase(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Finance Tenant")
        self.school = School.objects.create(tenant=self.tenant, name="Capital Business School")
        self.year = AcademicYear.objects.create(
            tenant=self.tenant, school=self.school, name="2026/2027", code="2026-2027",
            start_date="2026-09-01", end_date="2027-07-15"
        )
        self.person = Person.objects.create(
            tenant=self.tenant,
            person_number="PER-FIN-100",
            first_name="Victor",
            last_name="Stone",
            date_of_birth="2011-10-10",
            gender="male"
        )
        self.student = StudentProfile.objects.create(
            tenant=self.tenant,
            person=self.person,
            student_number="STU-2026-00777",
            admission_number="ADM-00777",
            current_school=self.school
        )
        self.client = APIClient()

    def test_billing_and_wallet_service_flow(self):
        # 1. Generate Invoice
        inv_res = BillingService.generate_invoice(
            student=self.student,
            school=self.school,
            academic_year=self.year,
            amount_due=500.00,
            items_list=[
                {"category": "tuition", "description": "Term 1 Tuition", "amount": 400.00},
                {"category": "ict", "description": "Computer Lab Levy", "amount": 100.00}
            ]
        )
        self.assertEqual(inv_res["status"], "success")
        invoice = Invoice.objects.get(id=inv_res["invoice_id"])
        self.assertEqual(invoice.status, "issued")

        # 2. Fund Student Wallet
        fund_res = WalletService.fund_wallet(student=self.student, amount=600.00, reference="DEP-TEST-001")
        self.assertEqual(fund_res["status"], "success")
        self.assertEqual(fund_res["new_balance"], 600.00)

        # 3. Pay Invoice from Wallet
        pay_res = WalletService.pay_invoice_from_wallet(student=self.student, invoice=invoice)
        self.assertEqual(pay_res["status"], "success")
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, "paid")
        self.assertEqual(pay_res["remaining_wallet_balance"], 100.00)
        self.assertTrue(pay_res["receipt_number"].startswith("RCT-"))

    def test_finance_api_endpoints(self):
        # 1. Generate Invoice API
        inv_url = '/efbm/api/v1/invoices/generate/'
        payload = {
            "student_id": str(self.student.id),
            "school_id": str(self.school.id),
            "academic_year_id": str(self.year.id),
            "amount_due": 250.00,
            "items": [{"category": "exam", "description": "Exam Fee", "amount": 250.00}]
        }
        resp = self.client.post(inv_url, payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        invoice_id = resp.data["data"]["invoice_id"]

        # 2. Fund Wallet API
        fund_url = '/efbm/api/v1/wallet/fund/'
        fund_payload = {
            "student_id": str(self.student.id),
            "amount": 300.00,
            "reference": "DEP-TEST-002"
        }
        fund_resp = self.client.post(fund_url, fund_payload, format='json')
        self.assertEqual(fund_resp.status_code, status.HTTP_200_OK)

        # 3. Pay Invoice API
        pay_url = '/efbm/api/v1/payments/'
        pay_payload = {
            "student_id": str(self.student.id),
            "invoice_id": invoice_id
        }
        pay_resp = self.client.post(pay_url, pay_payload, format='json')
        self.assertEqual(pay_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(pay_resp.data["status"], "success")
