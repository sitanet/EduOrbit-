import io
import requests
import logging
from django.core.files.base import ContentFile
from backend.apps.core.media.services.image_processing import ImageProcessor

logger = logging.getLogger(__name__)


import time

class BaseMediaProcessingService:
    """
    Generic Base Media Processing Service.
    Reusable pipeline across HR, Student, Guardian, Vendor, and Visitor photo engines.
    """

    @classmethod
    def download_image_from_url(cls, url: str, timeout: int = 15) -> bytes:
        """
        Download an image from a remote URL with connection timeout & validation.
        """
        headers = {'User-Agent': 'EduOrbit-ERP/3.0'}
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.content

    @classmethod
    def process_image_bytes(cls, image_bytes: bytes) -> dict:
        """
        Processes raw image bytes through the standard pipeline:
        1. Open & fix EXIF rotation / mode
        2. Strip EXIF privacy data
        3. Run face detection & auto-crop
        4. Compress main photo (600x600 JPEG @ 85%)
        5. Generate thumbnail (150x150 JPEG @ 85%)
        6. Compute SHA256 checksums
        7. Extract dimensions & processing metrics
        """
        start_time = time.time()
        img = ImageProcessor.open_image(image_bytes)
        clean_img = ImageProcessor.strip_exif(img)

        # Detect face & crop box
        cropped_img, face_detected = ImageProcessor.detect_face_and_crop(clean_img)

        # Compress main photo & generate thumbnail
        main_photo_bytes = ImageProcessor.compress_main_photo(cropped_img, max_dim=(600, 600), quality=85)
        thumbnail_bytes = ImageProcessor.generate_thumbnail(cropped_img, target_size=(150, 150), quality=85)
        sha256_hash = ImageProcessor.compute_sha256(main_photo_bytes)

        # Extract dimensions & metrics
        processed_img = ImageProcessor.open_image(main_photo_bytes)
        width, height = processed_img.size
        orig_size = len(image_bytes)
        compressed_size = len(main_photo_bytes)
        duration_ms = round((time.time() - start_time) * 1000, 2)
        compression_ratio = round((1 - (compressed_size / orig_size)) * 100, 2) if orig_size > 0 else 0.0

        return {
            "original_bytes": image_bytes,
            "main_photo_bytes": main_photo_bytes,
            "thumbnail_bytes": thumbnail_bytes,
            "sha256_hash": sha256_hash,
            "face_detected": face_detected,
            "width": width,
            "height": height,
            "size_bytes": compressed_size,
            "metrics": {
                "processing_time_ms": duration_ms,
                "original_size_bytes": orig_size,
                "compressed_size_bytes": compressed_size,
                "thumbnail_size_bytes": len(thumbnail_bytes),
                "compression_ratio_pct": compression_ratio,
                "processor_version": "1.0"
            }
        }
