from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from backend.apps.efbm.models import Invoice, Payment, StudentWallet, StudentLedger
from backend.apps.efbm.api.serializers import (
    InvoiceSerializer, PaymentSerializer, WalletSerializer, LedgerSerializer
)
from backend.apps.core.events import event_bus, DomainEvent

class InvoiceAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        invoices = Invoice.objects.filter(tenant=request.tenant)
        serializer = InvoiceSerializer(invoices, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = InvoiceSerializer(data=request.data)
        if serializer.is_valid():
            inv = serializer.save(tenant=request.tenant)
            event_bus.publish(DomainEvent("invoice.issued", tenant_id=str(request.tenant.id), data={"id": str(inv.id)}))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PaymentAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        payments = Payment.objects.filter(tenant=request.tenant)
        serializer = PaymentSerializer(payments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = PaymentSerializer(data=request.data)
        if serializer.is_valid():
            pay = serializer.save(tenant=request.tenant)
            
            # Post ledger transaction (receivable credit)
            if pay.invoice:
                student = pay.invoice.student
                prev_ledger = StudentLedger.objects.filter(student=student, tenant=request.tenant).order_by('-created_at').first()
                prev_bal = prev_ledger.balance_after if prev_ledger else 0.00
                new_bal = prev_bal - pay.amount
                
                StudentLedger.objects.create(
                    student=student,
                    tenant=request.tenant,
                    description=f"Fee Payment: Ref #{pay.reference}",
                    credit_amount=pay.amount,
                    balance_after=new_bal
                )
                
            event_bus.publish(DomainEvent("payment.received", tenant_id=str(request.tenant.id), data={"id": str(pay.id)}))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WalletAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        parent_id = request.query_params.get('parent_id')
        wallet = get_object_or_404(StudentWallet, parent_id=parent_id, tenant=request.tenant)
        serializer = WalletSerializer(wallet)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        parent_id = request.data.get('parent_id')
        amount = request.data.get('amount', 0)
        wallet, created = StudentWallet.objects.get_or_create(parent_id=parent_id, tenant=request.tenant)
        wallet.balance += float(amount)
        wallet.save()
        return Response({
            "parent_id": parent_id,
            "new_balance": str(wallet.balance)
        }, status=status.HTTP_200_OK)
