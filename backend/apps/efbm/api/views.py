from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from backend.apps.people.models import StudentProfile
from backend.apps.tenants.models import School
from backend.apps.academic.models import AcademicYear
from backend.apps.efbm.models import Invoice, StudentWallet
from backend.apps.efbm.services.billing import BillingService, WalletService

class InvoiceGenerateAPIView(APIView):
    def post(self, request):
        student_id = request.data.get('student_id')
        school_id = request.data.get('school_id')
        academic_year_id = request.data.get('academic_year_id')
        amount_due = request.data.get('amount_due', 0.00)
        items = request.data.get('items', [])

        try:
            student = StudentProfile.objects.get(id=student_id)
            school = School.objects.get(id=school_id)
            year = AcademicYear.objects.get(id=academic_year_id) if academic_year_id else AcademicYear.objects.first()
            res = BillingService.generate_invoice(
                student=student, school=school, academic_year=year, amount_due=amount_due, items_list=items
            )
            return Response({"status": "success", "data": res}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class InvoiceListAPIView(APIView):
    def get(self, request):
        student_id = request.query_params.get('student_id')
        invoices = Invoice.objects.all()
        if student_id:
            invoices = invoices.filter(student_id=student_id)

        data = [
            {
                "id": str(i.id),
                "invoice_number": i.invoice_number,
                "status": i.status,
                "student_number": i.student.student_number
            }
            for i in invoices
        ]
        return Response({"status": "success", "count": len(data), "data": data})


class PaymentCreateAPIView(APIView):
    def post(self, request):
        student_id = request.data.get('student_id')
        invoice_id = request.data.get('invoice_id')

        try:
            student = StudentProfile.objects.get(id=student_id)
            invoice = Invoice.objects.get(id=invoice_id)
            res = WalletService.pay_invoice_from_wallet(student=student, invoice=invoice)
            return Response({"status": "success" if res["status"] == "success" else "error", "data": res}, status=status.HTTP_200_OK if res["status"] == "success" else status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class WalletDetailAPIView(APIView):
    def get(self, request):
        student_id = request.query_params.get('student_id')
        try:
            wallet = StudentWallet.objects.get(student_id=student_id)
            return Response({
                "status": "success",
                "data": {
                    "student_number": wallet.student.student_number,
                    "balance": float(wallet.balance)
                }
            })
        except StudentWallet.DoesNotExist:
            return Response({"status": "error", "message": "Wallet not found."}, status=status.HTTP_404_NOT_FOUND)


class WalletFundAPIView(APIView):
    def post(self, request):
        student_id = request.data.get('student_id')
        amount = request.data.get('amount', 0.00)
        reference = request.data.get('reference')

        try:
            student = StudentProfile.objects.get(id=student_id)
            res = WalletService.fund_wallet(student=student, amount=amount, reference=reference)
            return Response({"status": "success", "data": res}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ==============================================================
# ENTERPRISE ACCOUNTING & FINANCIAL STATEMENT API VIEWS
# ==============================================================

from backend.apps.efbm.services.accounting import (
    JournalPostingService, GeneralLedgerService, FinancialStatementService
)

class JournalPostAPIView(APIView):
    def post(self, request):
        school_id = request.data.get('school_id')
        event_type = request.data.get('event_type', 'manual_journal')
        debit_account = request.data.get('debit_account')
        credit_account = request.data.get('credit_account')
        amount = request.data.get('amount', 0.00)

        try:
            school = School.objects.get(id=school_id)
            res = JournalPostingService.post_journal_entry(
                school=school,
                event_type=event_type,
                debit_account=debit_account,
                credit_account=credit_account,
                amount=amount
            )
            return Response({"status": "success", "data": res}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class TrialBalanceAPIView(APIView):
    def get(self, request):
        school_id = request.query_params.get('school_id')
        try:
            school = School.objects.get(id=school_id)
            res = GeneralLedgerService.get_trial_balance(school)
            return Response({"status": "success", "data": res}, status=status.HTTP_200_OK)
        except School.DoesNotExist:
            return Response({"status": "error", "message": "School not found."}, status=status.HTTP_404_NOT_FOUND)


class ProfitLossAPIView(APIView):
    def get(self, request):
        school_id = request.query_params.get('school_id')
        try:
            school = School.objects.get(id=school_id)
            res = FinancialStatementService.generate_profit_loss(school)
            return Response({"status": "success", "data": res}, status=status.HTTP_200_OK)
        except School.DoesNotExist:
            return Response({"status": "error", "message": "School not found."}, status=status.HTTP_404_NOT_FOUND)


class BalanceSheetAPIView(APIView):
    def get(self, request):
        school_id = request.query_params.get('school_id')
        try:
            school = School.objects.get(id=school_id)
            res = FinancialStatementService.generate_balance_sheet(school)
            return Response({"status": "success", "data": res}, status=status.HTTP_200_OK)
        except School.DoesNotExist:
            return Response({"status": "error", "message": "School not found."}, status=status.HTTP_404_NOT_FOUND)


# ==============================================================
# ENTERPRISE BUDGETING & FINANCIAL CONTROL API VIEWS
# ==============================================================

from backend.apps.efbm.models import Budget
from backend.apps.efbm.services.budgeting import BudgetService, BudgetControlService

class BudgetCreateAPIView(APIView):
    def post(self, request):
        school_id = request.data.get('school_id')
        academic_year_id = request.data.get('academic_year_id')
        name = request.data.get('name')
        items = request.data.get('items', [])

        try:
            school = School.objects.get(id=school_id)
            year = AcademicYear.objects.get(id=academic_year_id) if academic_year_id else AcademicYear.objects.first()
            res = BudgetService.create_budget(school=school, academic_year=year, name=name, items_list=items)
            return Response({"status": "success", "data": res}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class BudgetApproveAPIView(APIView):
    def post(self, request):
        budget_id = request.data.get('budget_id')
        try:
            budget = Budget.objects.get(id=budget_id)
            res = BudgetService.approve_budget(budget=budget)
            return Response({"status": "success", "data": res}, status=status.HTTP_200_OK)
        except Budget.DoesNotExist:
            return Response({"status": "error", "message": "Budget not found."}, status=status.HTTP_404_NOT_FOUND)


class BudgetUtilizationAPIView(APIView):
    def get(self, request):
        budget_id = request.query_params.get('budget_id')
        try:
            budget = Budget.objects.get(id=budget_id)
            res = BudgetControlService.get_budget_utilization(budget=budget)
            return Response({"status": "success", "data": res}, status=status.HTTP_200_OK)
        except Budget.DoesNotExist:
            return Response({"status": "error", "message": "Budget not found."}, status=status.HTTP_404_NOT_FOUND)


class BudgetVarianceAPIView(APIView):
    def get(self, request):
        budget_id = request.query_params.get('budget_id')
        try:
            budget = Budget.objects.get(id=budget_id)
            res = BudgetControlService.get_budget_utilization(budget=budget)
            return Response({
                "status": "success",
                "data": {
                    "budget_name": res["budget_name"],
                    "allocated": res["total_allocated"],
                    "spent": res["total_spent"],
                    "variance": res["total_available"]
                }
            }, status=status.HTTP_200_OK)
        except Budget.DoesNotExist:
            return Response({"status": "error", "message": "Budget not found."}, status=status.HTTP_404_NOT_FOUND)


