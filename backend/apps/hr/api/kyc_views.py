import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.core.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from backend.apps.hr.services.kyc import get_kyc_provider
from backend.apps.hr.services.duplicate_detector import DuplicateDetectionService
from backend.apps.hr.models.onboarding_draft import OnboardingDraft
from backend.apps.hr.permissions import IsHRAdmin

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


from django.core.exceptions import ValidationError

@method_decorator(csrf_exempt, name='dispatch')
class AutoSaveDraftAPIView(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body.decode('utf-8'))
            current_step = data.get('current_step', 1)
            draft_data = data.get('draft_data', {})
            draft_id = data.get('draft_id')
            
            # Get tenant from request (set by TenantMiddleware)
            tenant = getattr(request, 'tenant', None)
            if not tenant:
                return JsonResponse({"status": "error", "message": "Tenant context required"}, status=400)
            
            draft = None
            if draft_id and str(draft_id).strip().lower() not in ['', 'null', 'undefined', 'none']:
                try:
                    draft = OnboardingDraft.objects.get(draft_id=draft_id, tenant=tenant)
                except (OnboardingDraft.DoesNotExist, ValueError, ValidationError):
                    draft = None

            if not draft:
                draft = OnboardingDraft.objects.create(tenant=tenant)
                
            draft.current_step = current_step
            draft.draft_data = draft_data
            draft.save()

            return JsonResponse({
                "status": "success",
                "draft_id": str(draft.draft_id),
                "current_step": draft.current_step,
                "auto_saved_at": draft.auto_saved_at.strftime("%H:%M:%S") if draft.auto_saved_at else "N/A"
            })
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"AutoSaveDraft ERROR: {error_details}")
            return JsonResponse({"status": "error", "message": str(e), "details": error_details}, status=500)


class SubmitOnboardingAPIView(APIView):
    """
    Final submission endpoint for completed onboarding wizard.
    Converts OnboardingDraft into a full Employee record.
    
    POST /hr/api/v1/onboarding/submit/
    Body: {"draft_id": "uuid-string"}
    
    Returns:
        Success: {"status": "success", "employee_number": "EMP-XXX", ...}
        Error: {"status": "error", "message": "...", "validation_errors": [...]}
    
    Security:
        - Requires authentication (IsAuthenticated)
        - Requires HR Admin permission (IsHRAdmin)
        - CSRF protection enabled (via SessionAuthentication)
        - Tenant isolation enforced
    """
    permission_classes = [IsAuthenticated, IsHRAdmin]
    
    def post(self, request, *args, **kwargs):
        try:
            from backend.apps.hr.services.employee import EmployeeService
            from backend.apps.core.services.notifications import UnifiedNotificationService
            
            draft_id = request.data.get('draft_id')
            
            if not draft_id:
                return Response({
                    "status": "error",
                    "message": "draft_id is required"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get tenant from request (set by TenantMiddleware)
            tenant = getattr(request, 'tenant', None)
            if not tenant:
                return Response({
                    "status": "error",
                    "message": "Tenant context required"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get actor person for audit (HR admin who approved)
            actor_person = getattr(request.user, 'person_profile', None)
            
            # Retrieve draft
            try:
                draft = OnboardingDraft.objects.get(draft_id=draft_id, tenant=tenant)
            except OnboardingDraft.DoesNotExist:
                return Response({
                    "status": "error",
                    "message": f"Onboarding draft not found: {draft_id}"
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Mark draft complete for submission
            draft.is_completed = True
            draft.save()
            
            # Create employee from draft
            try:
                employee = EmployeeService.create_employee_from_onboarding_draft(
                    tenant=tenant,
                    draft=draft,
                    actor_person=actor_person
                )
            except ValidationError as ve:
                return Response({
                    "status": "error",
                    "message": str(ve),
                    "validation_errors": ve.messages if hasattr(ve, 'messages') else [str(ve)]
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Send welcome notification (outside transaction)
            try:
                person = employee.person
                user = person.user
                UnifiedNotificationService.send_notification(
                    recipient=person.first_name,
                    title="Welcome to EduOrbit HR",
                    message=f"Your employee account has been created. Employee Number: {employee.employee_number}. Username: {user.username}. Temporary Password: ChangeMe123!",
                    channels=['in_app', 'email'],
                    metadata={'email': user.email}
                )
            except Exception as notif_err:
                # Log but don't fail - notification is non-critical
                print(f"Notification error (non-critical): {notif_err}")
            
            # Return success response
            return Response({
                "status": "success",
                "message": "Employee onboarding completed successfully",
                "employee_number": employee.employee_number,
                "employee_id": str(employee.id),
                "person_number": employee.person.person_number,
                "username": employee.person.user.username,
                "email": employee.person.user.email,
                "job_title": employee.job_title,
                "department": employee.department_name
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"SubmitOnboarding ERROR: {error_details}")
            return Response({
                "status": "error",
                "message": "Internal server error during onboarding submission",
                "details": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


from rest_framework.parsers import MultiPartParser, FormParser, JSONParser


class ReplaceEmployeePhotoAPIView(APIView):
    """
    API View to replace an employee's official active photograph.
    POST /hr/api/v1/employees/<employee_id>/replace-photo/
    
    Accepts:
        - Multipart form: file/photo (JPG, PNG, JPEG, max 2MB)
        - Body JSON: photo_url, reason
    
    Permissions:
        - IsAuthenticated
        - IsHRAdmin
    """
    permission_classes = [IsAuthenticated, IsHRAdmin]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def post(self, request, employee_id, *args, **kwargs):
        try:
            from backend.apps.hr.models.employee import EmployeeProfile
            from backend.apps.hr.services.photo_service import EmployeePhotoService

            tenant = getattr(request, 'tenant', None)
            if not tenant and hasattr(request.user, 'person_profile') and request.user.person_profile:
                tenant = request.user.person_profile.tenant

            if not tenant:
                return Response({"status": "error", "message": "Tenant context required"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                employee = EmployeeProfile.objects.get(id=employee_id, tenant=tenant)
            except EmployeeProfile.DoesNotExist:
                return Response({"status": "error", "message": f"Employee not found: {employee_id}"}, status=status.HTTP_404_NOT_FOUND)

            actor_person = getattr(request.user, 'person_profile', None)
            file_obj = request.FILES.get('photo') or request.FILES.get('file')
            photo_url = request.data.get('photo_url')
            reason = request.data.get('reason') or request.POST.get('reason') or "Official photo replacement"

            if not file_obj and not photo_url:
                return Response({"status": "error", "message": "Photo file or photo_url is required"}, status=status.HTTP_400_BAD_REQUEST)

            # Validate file size <= 2MB (2 * 1024 * 1024 bytes)
            if file_obj and file_obj.size > 2 * 1024 * 1024:
                return Response({"status": "error", "message": "File size exceeds maximum allowed limit of 2 MB"}, status=status.HTTP_400_BAD_REQUEST)

            # Validate file extension
            if file_obj:
                ext = file_obj.name.split('.')[-1].lower()
                if ext not in ['jpg', 'jpeg', 'png']:
                    return Response({"status": "error", "message": "Invalid file format. Only JPG, JPEG, and PNG files are allowed."}, status=status.HTTP_400_BAD_REQUEST)

            target_payload = file_obj if file_obj else photo_url
            source = "HR_UPLOAD" if file_obj else "DOJAH_NIN"

            updated_employee = EmployeePhotoService.replace_employee_photo(
                employee=employee,
                file_obj_or_bytes_or_url=target_payload,
                source=source,
                provider="HR_MANUAL" if file_obj else "DOJAH",
                method="UPLOAD" if file_obj else "NIN",
                actor_person=actor_person,
                reason=reason
            )

            photo_url_str = updated_employee.photo.url if updated_employee.photo else ""
            thumb_url_str = updated_employee.photo_thumbnail.url if updated_employee.photo_thumbnail else ""

            return Response({
                "status": "success",
                "message": "Employee photo replaced successfully",
                "employee_id": str(updated_employee.id),
                "employee_number": updated_employee.employee_number,
                "photo_url": photo_url_str,
                "thumbnail_url": thumb_url_str,
                "photo_source": updated_employee.photo_source,
                "photo_verified_at": updated_employee.photo_verified_at.strftime("%Y-%m-%d %H:%M:%S") if updated_employee.photo_verified_at else None,
                "photo_last_updated": updated_employee.photo_last_updated.strftime("%Y-%m-%d %H:%M:%S") if updated_employee.photo_last_updated else None
            }, status=status.HTTP_200_OK)

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"ReplaceEmployeePhoto ERROR: {error_details}")
            return Response({"status": "error", "message": "Failed to replace employee photo", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProtectedEmployeePhotoView(View):
    """
    NDPA Protected Media View for streaming employee photo or thumbnail.
    GET /hr/api/v1/employees/<employee_id>/photo/ (or ?type=thumbnail)
    Includes ETag caching support for bandwidth optimization.
    """
    def get(self, request, employee_id, *args, **kwargs):
        try:
            from backend.apps.hr.models.employee import EmployeeProfile
            from django.http import HttpResponse, HttpResponseNotModified, Http404
            from django.core.files.storage import default_storage

            if not request.user.is_authenticated:
                return HttpResponse("Unauthorized", status=401)

            tenant = getattr(request, 'tenant', None)
            if not tenant and hasattr(request.user, 'person_profile') and request.user.person_profile:
                tenant = request.user.person_profile.tenant

            query = EmployeeProfile.objects.filter(id=employee_id)
            if tenant:
                query = query.filter(tenant=tenant)

            employee = query.first()
            if not employee:
                raise Http404("Employee profile not found")

            is_thumb = request.GET.get('type') == 'thumbnail'
            target_field = employee.photo_thumbnail if is_thumb else employee.photo

            if not target_field or not target_field.name:
                raise Http404("No photo uploaded for this employee")

            if not default_storage.exists(target_field.name):
                raise Http404("Photo file not found in storage")

            # Check ETag based on photo_hash
            etag = f'"{employee.photo_hash or employee.id}"'
            if_none_match = request.headers.get('If-None-Match') or request.META.get('HTTP_IF_NONE_MATCH')
            if if_none_match == etag:
                response = HttpResponseNotModified()
                response['ETag'] = etag
                response['Cache-Control'] = 'private, max-age=86400'
                return response

            file_data = default_storage.open(target_field.name, 'rb').read()
            response = HttpResponse(file_data, content_type="image/jpeg")
            response['ETag'] = etag
            response['Cache-Control'] = 'private, max-age=86400'
            return response

        except Http404 as h4:
            from django.http import Http404
            raise h4
        except Exception as e:
            from django.http import HttpResponseServerError
            return HttpResponseServerError(f"Error serving photo: {str(e)}")

