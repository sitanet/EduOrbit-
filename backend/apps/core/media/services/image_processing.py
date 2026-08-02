import io
import hashlib
import logging
from PIL import Image, ImageOps

logger = logging.getLogger(__name__)

# Try importing OpenCV for face detection
try:
    import cv2
    import numpy as np
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False

# Try importing pillow_heif for HEIC support
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    HAS_HEIF = True
except ImportError:
    HAS_HEIF = False


class ImageProcessor:
    """
    Core Image Processing Engine for EduOrbit ERP.
    Handles EXIF stripping, face detection/cropping, JPEG compression (600x600),
    thumbnailing (150x150), SHA256 checksums, and image validation.
    """

    @staticmethod
    def open_image(image_bytes_or_file) -> Image.Image:
        """
        Safely open an image from bytes or file-like object.
        Strips EXIF auto-rotation orientation if present.
        """
        if isinstance(image_bytes_or_file, bytes):
            stream = io.BytesIO(image_bytes_or_file)
        else:
            image_bytes_or_file.seek(0)
            stream = io.BytesIO(image_bytes_or_file.read())
            image_bytes_or_file.seek(0)

        img = Image.open(stream)
        # Apply EXIF transpose to fix rotation
        try:
            img = ImageOps.exif_transpose(img)
        except Exception:
            pass

        # Convert to RGB mode (drops alpha channel or CMYK)
        if img.mode in ('RGBA', 'LA', 'P', 'CMYK'):
            img = img.convert('RGB')
        return img

    @staticmethod
    def strip_exif(img: Image.Image) -> Image.Image:
        """
        Return a copy of the PIL Image with EXIF metadata stripped.
        """
        data = list(img.getdata())
        clean_img = Image.new(img.mode, img.size)
        clean_img.putdata(data)
        return clean_img

    @staticmethod
    def detect_face_and_crop(img: Image.Image, padding_factor: float = 0.3) -> tuple[Image.Image, bool]:
        """
        Detect face using OpenCV Haar Cascade if available.
        Crops image around face with padding.
        Returns: (cropped_image, face_detected_bool)
        """
        if not HAS_OPENCV or not hasattr(cv2, 'CascadeClassifier'):
            logger.debug("OpenCV CascadeClassifier not available, returning original uncropped image")
            return img, False

        try:
            # Convert PIL image to cv2 numpy array (RGB to BGR)
            np_img = np.array(img)
            gray = cv2.cvtColor(np_img, cv2.COLOR_RGB2GRAY)

            # Load default frontal face cascade classifier
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))

            if len(faces) == 0:
                logger.info("No face detected by OpenCV cascade classifier")
                return img, False

            # Select the primary (largest) face
            x, y, w, h = max(faces, key=lambda rect: rect[2] * rect[3])
            img_w, img_h = img.size

            # Apply padding around face box
            pad_w = int(w * padding_factor)
            pad_h = int(h * padding_factor)

            crop_x1 = max(0, x - pad_w)
            crop_y1 = max(0, y - pad_h)
            crop_x2 = min(img_w, x + w + pad_w)
            crop_y2 = min(img_h, y + h + pad_h)

            cropped = img.crop((crop_x1, crop_y1, crop_x2, crop_y2))
            return cropped, True
        except Exception as e:
            logger.warning(f"Error during face detection: {e}")
            return img, False

    @staticmethod
    def compress_main_photo(img: Image.Image, max_dim: tuple[int, int] = (600, 600), quality: int = 85) -> bytes:
        """
        Compress image into a max 600x600 RGB JPEG at 85% quality.
        Returns JPEG bytes.
        """
        img_copy = img.copy()
        img_copy.thumbnail(max_dim, Image.Resampling.LANCZOS)

        out = io.BytesIO()
        img_copy.save(out, format='JPEG', quality=quality, optimize=True)
        return out.getvalue()

    @staticmethod
    def generate_thumbnail(img: Image.Image, target_size: tuple[int, int] = (150, 150), quality: int = 85) -> bytes:
        """
        Generate a 150x150 square thumbnail with centered crop.
        Returns JPEG bytes.
        """
        # Center crop to 1:1 aspect ratio
        width, height = img.size
        min_dim = min(width, height)
        left = (width - min_dim) / 2
        top = (height - min_dim) / 2
        right = (width + min_dim) / 2
        bottom = (height + min_dim) / 2

        cropped = img.crop((left, top, right, bottom))
        resized = cropped.resize(target_size, Image.Resampling.LANCZOS)

        out = io.BytesIO()
        resized.save(out, format='JPEG', quality=quality, optimize=True)
        return out.getvalue()

    @staticmethod
    def compute_sha256(data_bytes: bytes) -> str:
        """Compute SHA256 checksum string."""
        return hashlib.sha256(data_bytes).hexdigest()
