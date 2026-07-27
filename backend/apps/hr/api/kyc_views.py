import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from backend.apps.hr.services.kyc import get_kyc_provider
from backend.apps.hr.services.duplicate_detector import DuplicateDetectionService
from backend.apps.hr.models.onboarding_draft import OnboardingDraft

@method_decorator(csrf_exempt, name='dispatch')
class VerifyNINAPIView(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body.decode('utf-8'))
            nin = data.get('nin')
            if not nin:
                return JsonResponse({"status": "error", "message": "NIN is required"}, status=400)
            provider = get_kyc_provider()
            res = provider.verify_nin(nin)
            return JsonResponse(res)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class VerifyBVNAPIView(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body.decode('utf-8'))
            bvn = data.get('bvn')
            if not bvn:
                return JsonResponse({"status": "error", "message": "BVN is required"}, status=400)
            provider = get_kyc_provider()
            res = provider.verify_bvn(bvn)
            return JsonResponse(res)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ResolveBankAccountAPIView(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body.decode('utf-8'))
            account_number = data.get('account_number')
            bank_code = data.get('bank_code', '058')
            if not account_number:
                return JsonResponse({"status": "error", "message": "Account Number is required"}, status=400)
            provider = get_kyc_provider()
            res = provider.resolve_bank_account(bank_code, account_number)
            return JsonResponse(res)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class AutoSaveDraftAPIView(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body.decode('utf-8'))
            current_step = data.get('current_step', 1)
            draft_data = data.get('draft_data', {})
            draft_id = data.get('draft_id')
            
            if draft_id:
                draft, _ = OnboardingDraft.objects.get_or_create(draft_id=draft_id)
            else:
                draft = OnboardingDraft.objects.create()
                
            draft.current_step = current_step
            draft.draft_data = draft_data
            draft.save()

            return JsonResponse({
                "status": "success",
                "draft_id": str(draft.draft_id),
                "current_step": draft.current_step,
                "auto_saved_at": draft.auto_saved_at.strftime("%H:%M:%S")
            })
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
