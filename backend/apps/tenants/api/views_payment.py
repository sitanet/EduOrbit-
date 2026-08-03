"""
Gateway-Agnostic REST API Views for EduOrbit Subscription Payments & Webhooks.
Supports Paystack, OPay, and Manual Payment Processing.
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from backend.apps.tenants.models import SubscriptionInvoice, SubscriptionPayment
from backend.apps.tenants.services.payment_service import PaymentService
from backend.apps.tenants.services.webhook_service import WebhookService


class PaymentInitializeAPIView(APIView):
    """
    POST /api/v1/tenants/billing/payment/initialize/
    Initializes payment for an invoice. Accepts selected gateway ('PAYSTACK' or 'OPAY').
    """
    permission_classes = [AllowAny]

    def post(self, request):
        invoice_id = request.data.get('invoice_id')
        provider_name = request.data.get('provider_name', 'PAYSTACK')
        callback_url = request.data.get('callback_url')

        if not invoice_id:
            return Response({"success": False, "message": "invoice_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            invoice = SubscriptionInvoice.objects.get(id=invoice_id)
            res = PaymentService.initialize_payment(
                invoice=invoice,
                provider_name=provider_name,
                callback_url=callback_url,
                actor=request.user if request.user.is_authenticated else None
            )
            return Response(res.to_dict(), status=status.HTTP_200_OK if res.success else status.HTTP_400_BAD_REQUEST)
        except SubscriptionInvoice.DoesNotExist:
            return Response({"success": False, "message": "Invoice not found."}, status=status.HTTP_404_NOT_FOUND)


class PaymentVerifyAPIView(APIView):
    """
    POST /api/v1/tenants/billing/payment/verify/
    Verifies payment with gateway using reference.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        payment_reference = request.data.get('payment_reference')
        provider_name = request.data.get('provider_name', 'PAYSTACK')

        if not payment_reference:
            return Response({"success": False, "message": "payment_reference is required."}, status=status.HTTP_400_BAD_REQUEST)

        res = PaymentService.verify_and_complete_payment(
            payment_reference=payment_reference,
            provider_name=provider_name
        )
        return Response(res.to_dict(), status=status.HTTP_200_OK if res.success else status.HTTP_400_BAD_REQUEST)


class PaystackWebhookAPIView(APIView):
    """
    POST /api/v1/tenants/billing/payment/webhook/paystack/
    Webhook listener for Paystack payment callbacks with HMAC SHA512 signature verification.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        payload = request.data
        signature_header = request.headers.get('x-paystack-signature', '')

        res = WebhookService.process_gateway_webhook(
            provider_name='PAYSTACK',
            payload=payload,
            signature_header=signature_header
        )
        return Response(res.to_dict(), status=status.HTTP_200_OK if res.success else status.HTTP_400_BAD_REQUEST)


class OPayWebhookAPIView(APIView):
    """
    POST /api/v1/tenants/billing/payment/webhook/opay/
    Webhook listener for OPay payment callbacks with signature verification.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        payload = request.data
        signature_header = request.headers.get('Authorization', request.headers.get('x-opay-signature', ''))

        res = WebhookService.process_gateway_webhook(
            provider_name='OPAY',
            payload=payload,
            signature_header=signature_header
        )
        return Response(res.to_dict(), status=status.HTTP_200_OK if res.success else status.HTTP_400_BAD_REQUEST)


class ManualPaymentAPIView(APIView):
    """
    POST /api/v1/tenants/billing/manual-payment/
    Processes manual offline payments (CASH, POS, BANK_TRANSFER, CHEQUE) on behalf of parents.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        invoice_id = request.data.get('invoice_id')
        payment_method = request.data.get('payment_method', 'CASH')
        payment_reference = request.data.get('payment_reference')

        if not invoice_id:
            return Response({"success": False, "message": "invoice_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            invoice = SubscriptionInvoice.objects.get(id=invoice_id)
            res = PaymentService.process_manual_payment(
                invoice=invoice,
                payment_method=payment_method,
                payment_reference=payment_reference,
                actor=request.user if request.user.is_authenticated else None,
                paid_on_behalf=True
            )
            return Response(res.to_dict(), status=status.HTTP_200_OK if res.success else status.HTTP_400_BAD_REQUEST)
        except SubscriptionInvoice.DoesNotExist:
            return Response({"success": False, "message": "Invoice not found."}, status=status.HTTP_404_NOT_FOUND)


class PaymentStatusAPIView(APIView):
    """
    GET /api/v1/tenants/billing/payment-status/
    Retrieves payment transaction status.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        reference = request.query_params.get('reference')
        if not reference:
            return Response({"success": False, "message": "reference parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            payment = SubscriptionPayment.objects.get(reference=reference)
            data = {
                "reference": payment.reference,
                "invoice_number": payment.invoice.invoice_number if payment.invoice else None,
                "amount": float(payment.amount),
                "gateway": payment.gateway,
                "payment_method": payment.payment_method,
                "status": payment.status,
                "receipt_number": payment.receipt_number,
                "paid_at": str(payment.paid_at) if payment.paid_at else None
            }
            return Response({"success": True, "message": "Payment status retrieved.", "data": data})
        except SubscriptionPayment.DoesNotExist:
            return Response({"success": False, "message": "Payment transaction reference not found."}, status=status.HTTP_404_NOT_FOUND)
