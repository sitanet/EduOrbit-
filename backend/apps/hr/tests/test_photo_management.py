import io
import uuid
from PIL import Image
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from backend.apps.tenants.models import Tenant
from backend.apps.people.models import Person
from backend.apps.hr.models.employee import EmployeeProfile, HRAuditLog
from backend.apps.hr.services.photo_service import EmployeePhotoService
from backend.apps.core.media.services.base_media_service import BaseMediaProcessingService

User = get_user_model()


class EmployeePhotoManagementTests(TestCase):
    """
    Unit & Integration Tests for Phase 12.4.4A - Enterprise Employee Photo Management.
    """

    def setUp(self):
        self.client = Client()
        self.tenant = Tenant.objects.create(name="Photo Test Academy", is_active=True)

        # Create HR Admin User & Person
        self.hr_user = User.objects.create_user(
            username="photoadmin",
            email="photoadmin@test.com",
            password="Password123!",
            is_staff=True
        )
        self.hr_person = Person.objects.create(
            tenant=self.tenant,
            person_number="PER-001",
            first_name="Admin",
            last_name="Officer",
            gender="female",
            date_of_birth="1988-04-12",
            user=self.hr_user
        )

        # Create Target Employee Profile & Person
        self.emp_user = User.objects.create_user(
            username="johnstaff",
            email="johnstaff@test.com",
            password="Password123!"
        )
        self.emp_person = Person.objects.create(
            tenant=self.tenant,
            person_number="PER-002",
            first_name="John",
            last_name="Doe",
            gender="male",
            date_of_birth="1992-08-15",
            user=self.emp_user
        )
        self.employee = EmployeeProfile.objects.create(
            tenant=self.tenant,
            person=self.emp_person,
            employee_number="EMP-TEST-001",
            job_title="Senior Lecturer",
            salary_grade="grade_3",
            status="active"
        )

        # Generate a sample 400x400 red test image
        img = Image.new('RGB', (400, 400), color='red')
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG')
        self.sample_image_bytes = img_byte_arr.getvalue()

    def test_base_media_processing_pipeline(self):
        """Test image compression, thumbnail generation, and SHA256 checksum computation"""
        processed = BaseMediaProcessingService.process_image_bytes(self.sample_image_bytes)

        self.assertIn("main_photo_bytes", processed)
        self.assertIn("thumbnail_bytes", processed)
        self.assertIn("sha256_hash", processed)
        self.assertIsNotNone(processed["sha256_hash"])
        self.assertEqual(len(processed["sha256_hash"]), 64)

        # Verify thumbnail dimensions
        thumb_img = Image.open(io.BytesIO(processed["thumbnail_bytes"]))
        self.assertEqual(thumb_img.size, (150, 150))

    def test_employee_photo_service_replacement_and_audit(self):
        """Test EmployeePhotoService photo replacement enforcing single active photo and audit log generation"""
        updated_emp = EmployeePhotoService.replace_employee_photo(
            employee=self.employee,
            file_obj_or_bytes_or_url=self.sample_image_bytes,
            source="HR_UPLOAD",
            provider="HR_MANUAL",
            method="UPLOAD",
            actor_person=self.hr_person,
            reason="Government photo outdated"
        )

        self.assertIsNotNone(updated_emp.photo)
        self.assertIsNotNone(updated_emp.photo_thumbnail)
        self.assertIsNotNone(updated_emp.original_photo)
        self.assertEqual(updated_emp.photo_source, "HR_UPLOAD")
        self.assertEqual(updated_emp.photo_replacement_reason, "Government photo outdated")
        self.assertEqual(updated_emp.photo_updated_by, self.hr_person)

        # Verify HRAuditLog entry created
        audit_log = HRAuditLog.objects.filter(
            model_affected="EmployeeProfile",
            object_id=str(self.employee.id),
            event_type="employee.photo_replaced"
        ).first()

        self.assertIsNotNone(audit_log)
        self.assertEqual(audit_log.reason, "Government photo outdated")
        self.assertEqual(audit_log.actor, self.hr_person)

    def test_replace_photo_api_success(self):
        """Test POST /hr/api/v1/employees/<id>/replace-photo/ endpoint with valid file upload"""
        self.client.login(username="photoadmin", password="Password123!")

        upload_file = SimpleUploadedFile(
            name="new_passport.jpg",
            content=self.sample_image_bytes,
            content_type="image/jpeg"
        )

        response = self.client.post(
            f"/hr/api/v1/employees/{self.employee.id}/replace-photo/",
            {"photo": upload_file, "reason": "Replaced blurry photo"},
            HTTP_HOST="test.localhost"
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["employee_id"], str(self.employee.id))

        self.employee.refresh_from_db()
        self.assertIsNotNone(self.employee.photo)

    def test_replace_photo_api_oversized_file_rejection(self):
        """Test POST replace photo endpoint rejects files larger than 2 MB"""
        self.client.login(username="photoadmin", password="Password123!")

        # Create dummy oversized file (2.5 MB)
        large_bytes = b"0" * (2500 * 1024)
        large_file = SimpleUploadedFile("large_image.jpg", large_bytes, content_type="image/jpeg")

        response = self.client.post(
            f"/hr/api/v1/employees/{self.employee.id}/replace-photo/",
            {"photo": large_file, "reason": "Oversized upload"},
            HTTP_HOST="test.localhost"
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("exceeds maximum allowed limit", data["message"])

    def test_replace_photo_api_invalid_extension_rejection(self):
        """Test POST replace photo endpoint rejects non-image formats (.txt)"""
        self.client.login(username="photoadmin", password="Password123!")

        txt_file = SimpleUploadedFile("document.txt", b"Hello world", content_type="text/plain")

        response = self.client.post(
            f"/hr/api/v1/employees/{self.employee.id}/replace-photo/",
            {"photo": txt_file, "reason": "Invalid doc format"},
            HTTP_HOST="test.localhost"
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("Invalid file format", data["message"])

    def test_protected_photo_stream_view(self):
        """Test GET /hr/api/v1/employees/<id>/photo/ streams protected photo data with ETag support"""
        # Upload photo first
        updated_emp = EmployeePhotoService.replace_employee_photo(
            employee=self.employee,
            file_obj_or_bytes_or_url=self.sample_image_bytes,
            actor_person=self.hr_person
        )

        self.assertIsNotNone(updated_emp.photo_hash)
        self.assertEqual(len(updated_emp.photo_hash), 64)
        self.assertGreater(updated_emp.photo_width, 0)
        self.assertGreater(updated_emp.photo_height, 0)
        self.assertGreater(updated_emp.photo_size, 0)
        self.assertIn("processing_time_ms", updated_emp.photo_processing_metrics)

        self.client.login(username="photoadmin", password="Password123!")
        response = self.client.get(f"/hr/api/v1/employees/{self.employee.id}/photo/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/jpeg")
        self.assertIn("private, max-age=86400", response["Cache-Control"])
        self.assertIn("ETag", response)

        # Test HTTP 304 Not Modified when ETag matches If-None-Match
        etag = response["ETag"]
        cached_response = self.client.get(
            f"/hr/api/v1/employees/{self.employee.id}/photo/",
            HTTP_IF_NONE_MATCH=etag
        )
        self.assertEqual(cached_response.status_code, 304)

    def test_staff_id_card_view_renders(self):
        """Test GET /hr/admin/employees/<id>/id-card/ renders printable ID card"""
        self.client.login(username="photoadmin", password="Password123!")
        response = self.client.get(f"/hr/admin/employees/{self.employee.id}/id-card/", HTTP_HOST="test.localhost")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "hr/admin/id_card.html")
        self.assertContains(response, self.employee.employee_number)
        self.assertContains(response, "Print ID Card")
