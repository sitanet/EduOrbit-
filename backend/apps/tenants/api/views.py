from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from backend.apps.tenants.models import Tenant, SubscriptionPlan, TenantSubscription
from backend.apps.tenants.services.subscription import SubscriptionService, SubscriptionValidationService
from backend.apps.tenants.services.gateways import OPayGateway, PaystackGateway

class SubscriptionPlanListAPIView(APIView):
    def get(self, request):
        plans = SubscriptionPlan.objects.filter(is_active=True)
        data = [
            {
                "id": str(p.id),
                "name": p.name,
                "description": p.description,
                "billing_model": p.billing_model,
                "monthly_price": float(p.monthly_price),
                "termly_price": float(p.termly_price),
                "yearly_price": float(p.yearly_price),
                "max_students": p.max_students,
                "max_staff": p.max_staff
            }
            for p in plans
        ]
        return Response({"status": "success", "count": len(data), "data": data})


class SubscriptionSubscribeAPIView(APIView):
    def post(self, request):
        tenant_id = request.data.get('tenant_id')
        plan_id = request.data.get('plan_id')
        billing_cycle = request.data.get('billing_cycle', 'MONTHLY')
        billing_model = request.data.get('billing_model', 'SCHOOL_PAY')

        try:
            tenant = Tenant.objects.get(id=tenant_id)
            plan = SubscriptionPlan.objects.get(id=plan_id)
            res = SubscriptionService.create_tenant_subscription(
                tenant=tenant, plan=plan, billing_cycle=billing_cycle, billing_model=billing_model
            )
            return Response({"status": "success", "data": res}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class SubscriptionRenewAPIView(APIView):
    def post(self, request):
        subscription_id = request.data.get('subscription_id')
        payment_reference = request.data.get('payment_reference')

        try:
            sub = TenantSubscription.objects.get(id=subscription_id)
            res = SubscriptionService.renew_subscription(subscription=sub, payment_reference=payment_reference)
            return Response({"status": "success", "data": res}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class SubscriptionStatusAPIView(APIView):
    def get(self, request):
        tenant_id = request.query_params.get('tenant_id')
        try:
            tenant = Tenant.objects.get(id=tenant_id)
            res = SubscriptionValidationService.validate_tenant_access(tenant=tenant)
            return Response({"status": "success", "data": res}, status=status.HTTP_200_OK)
        except Tenant.DoesNotExist:
            return Response({"status": "error", "message": "Tenant not found."}, status=status.HTTP_404_NOT_FOUND)


class OPayWebhookAPIView(APIView):
    def post(self, request):
        payload = request.data
        gateway = OPayGateway()
        res = gateway.handle_webhook(payload)
        return Response({"status": "success", "data": res}, status=status.HTTP_200_OK)


class PaystackWebhookAPIView(APIView):
    def post(self, request):
        payload = request.data
        gateway = PaystackGateway()
        res = gateway.handle_webhook(payload)
        return Response({"status": "success", "data": res}, status=status.HTTP_200_OK)
