import io
import uuid
import logging
from django.utils import timezone
from django.core.files.base import ContentFile
from backend.apps.core.media.services.base_media_service import BaseMediaProcessingService
from backend.apps.hr.models.employee import HRAuditLog, EmployeeProfile

logger = logging.getLogger(__name__)


class EmployeePhotoService(BaseMediaProcessingService):
    """
    Enterprise Employee Photo Management Service (Phase 12.4.4A MVP).
    Handles Dojah image download, local processing (compression, face detection warning, thumbnailing),
    single active photo replacement, and audit log generation.
    """

    @classmethod
    def download_and_process_dojah_photo(cls, photo_url: str, provider: str = "DOJAH", method: str = "NIN", ref: str = None) -> dict:
        """
        Download Dojah photo URL and run image processing pipeline.
        Returns dict with ContentFile objects for Django model fields.
        """
        if not photo_url:
            return None

        try:
            raw_bytes = cls.download_image_from_url(photo_url)
            processed = cls.process_image_bytes(raw_bytes)

            original_file = ContentFile(raw_bytes, name=f"dojah_orig_{uuid.uuid4().hex[:6]}.jpg")
            main_photo_file = ContentFile(processed["main_photo_bytes"], name=f"dojah_photo_{uuid.uuid4().hex[:6]}.jpg")
            thumb_file = ContentFile(processed["thumbnail_bytes"], name=f"dojah_thumb_{uuid.uuid4().hex[:6]}.jpg")

            return {
                "original_photo": original_file,
                "photo": main_photo_file,
                "photo_thumbnail": thumb_file,
                "sha256_hash": processed["sha256_hash"],
                "face_detected": processed["face_detected"],
                "width": processed.get("width"),
                "height": processed.get("height"),
                "size_bytes": processed.get("size_bytes"),
                "metrics": processed.get("metrics", {}),
                "photo_source": f"DOJAH_{method.upper()}" if method else "DOJAH",
                "photo_verification_provider": provider or "DOJAH",
                "photo_verification_method": method or "NIN",
                "photo_verification_reference": ref or ""
            }
        except Exception as e:
            logger.error(f"Failed to download and process Dojah photo from {photo_url}: {e}")
            return None

    @classmethod
    def process_uploaded_photo(cls, file_obj_or_bytes) -> dict:
        """
        Process an uploaded photo file or raw bytes.
        """
        if isinstance(file_obj_or_bytes, bytes):
            raw_bytes = file_obj_or_bytes
        else:
            file_obj_or_bytes.seek(0)
            raw_bytes = file_obj_or_bytes.read()
            file_obj_or_bytes.seek(0)

        processed = cls.process_image_bytes(raw_bytes)

        original_file = ContentFile(raw_bytes, name=f"upload_orig_{uuid.uuid4().hex[:6]}.jpg")
        main_photo_file = ContentFile(processed["main_photo_bytes"], name=f"upload_photo_{uuid.uuid4().hex[:6]}.jpg")
        thumb_file = ContentFile(processed["thumbnail_bytes"], name=f"upload_thumb_{uuid.uuid4().hex[:6]}.jpg")

        return {
            "original_photo": original_file,
            "photo": main_photo_file,
            "photo_thumbnail": thumb_file,
            "sha256_hash": processed["sha256_hash"],
            "face_detected": processed["face_detected"],
            "width": processed.get("width"),
            "height": processed.get("height"),
            "size_bytes": processed.get("size_bytes"),
            "metrics": processed.get("metrics", {}),
            "photo_source": "HR_UPLOAD"
        }

    @classmethod
    def replace_employee_photo(
        cls,
        employee: EmployeeProfile,
        file_obj_or_bytes_or_url,
        source: str = "HR_UPLOAD",
        provider: str = None,
        method: str = None,
        ref: str = None,
        actor_person=None,
        reason: str = None
    ) -> EmployeeProfile:
        """
        Replace an employee's official photo enforcing the SINGLE ACTIVE PHOTO policy.
        Old image is replaced on the model, and an audit trail entry is created in HRAuditLog.
        """
        if isinstance(file_obj_or_bytes_or_url, str) and (file_obj_or_bytes_or_url.startswith("http://") or file_obj_or_bytes_or_url.startswith("https://")):
            processed = cls.download_and_process_dojah_photo(file_obj_or_bytes_or_url, provider=provider or "DOJAH", method=method or "NIN", ref=ref)
        else:
            processed = cls.process_uploaded_photo(file_obj_or_bytes_or_url)

        if not processed:
            raise ValueError("Failed to process photo file or URL")

        # Record old values for audit
        old_values = {
            "photo": str(employee.photo) if employee.photo else "",
            "photo_thumbnail": str(employee.photo_thumbnail) if employee.photo_thumbnail else "",
            "photo_source": employee.photo_source or "",
            "photo_verification_provider": employee.photo_verification_provider or "",
            "photo_verification_reference": employee.photo_verification_reference or "",
            "photo_verified_at": employee.photo_verified_at.strftime("%Y-%m-%d %H:%M:%S") if employee.photo_verified_at else None
        }

        now = timezone.now()

        # Update single active photo on EmployeeProfile
        employee.original_photo.save(processed["original_photo"].name, processed["original_photo"], save=False)
        employee.photo.save(processed["photo"].name, processed["photo"], save=False)
        employee.photo_thumbnail.save(processed["photo_thumbnail"].name, processed["photo_thumbnail"], save=False)

        employee.photo_hash = processed.get("sha256_hash")
        employee.photo_width = processed.get("width")
        employee.photo_height = processed.get("height")
        employee.photo_size = processed.get("size_bytes")
        employee.photo_processing_metrics = processed.get("metrics", {})
        employee.photo_source = processed.get("photo_source") or source
        employee.photo_status = "ACTIVE"
        employee.photo_verification_provider = processed.get("photo_verification_provider") or provider or "HR_MANUAL"
        employee.photo_verification_method = processed.get("photo_verification_method") or method or "HR_UPLOAD"
        employee.photo_verification_reference = processed.get("photo_verification_reference") or ref or ""
        employee.photo_verified_at = now
        employee.photo_last_updated = now
        if actor_person:
            employee.photo_updated_by = actor_person
        if reason:
            employee.photo_replacement_reason = reason

        employee.save()

        # Record Audit Trail in HRAuditLog
        HRAuditLog.objects.create(
            tenant=employee.tenant,
            actor=actor_person,
            event_type="employee.photo_replaced",
            model_affected="EmployeeProfile",
            object_id=str(employee.id),
            old_values=old_values,
            new_values={
                "photo": str(employee.photo),
                "photo_thumbnail": str(employee.photo_thumbnail),
                "photo_source": employee.photo_source,
                "photo_verification_provider": employee.photo_verification_provider,
                "photo_verification_reference": employee.photo_verification_reference,
                "updated_by": f"{actor_person.first_name} {actor_person.last_name}" if actor_person else "System"
            },
            reason=reason or "Official photo replacement"
        )

        return employee
