import os
import sys
import django

# Setup Django environment
backend_dir = r"c:\Users\user\Desktop\Development\SMS\backend"
sys.path.insert(0, backend_dir)
sys.path.insert(0, r"c:\Users\user\Desktop\Development\SMS")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.config.settings.local")
django.setup()

from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

from backend.apps.tenants.models import Tenant, School
from backend.apps.people.models import Person, StudentProfile
from backend.apps.academic.models import (
    Curriculum, AcademicYear, AcademicPeriod, EducationLevel,
    AcademicLevel, AcademicClass, Subject, GradebookEntry,
    StudentReportCard, BatchPromotionLog
)
from backend.apps.academic.services import GradebookService, ReportCardService, PromotionService

def run_tests():
    print("--- Running Direct Academic Enterprise Tests ---")
    
    tenant = Tenant.objects.first() or Tenant.objects.create(name="Test Tenant Direct")
    school = School.objects.filter(tenant=tenant).first() or School.objects.create(tenant=tenant, name="Academy High", code="academy-high")
    
    year, _ = AcademicYear.objects.get_or_create(
        tenant=tenant,
        school=school,
        code="2026-2027",
        defaults={
            'name': "2026/2027",
            'start_date': timezone.now().date(),
            'end_date': (timezone.now() + timedelta(days=365)).date(),
            'status': "active"
        }
    )
    period, _ = AcademicPeriod.objects.get_or_create(
        tenant=tenant,
        academic_year=year,
        name="Term 1",
        defaults={
            'order': 1,
            'start_date': timezone.now().date(),
            'end_date': (timezone.now() + timedelta(days=90)).date(),
            'status': "active"
        }
    )
    edu_level, _ = EducationLevel.objects.get_or_create(
        tenant=tenant,
        school=school,
        code="secondary",
        defaults={'name': "Secondary"}
    )
    acad_level, _ = AcademicLevel.objects.get_or_create(
        tenant=tenant,
        education_level=edu_level,
        code="jss-1",
        defaults={'name': "JSS 1"}
    )
    class_from, _ = AcademicClass.objects.get_or_create(
        tenant=tenant,
        academic_level=acad_level,
        name="JSS 1 Gold"
    )
    class_to, _ = AcademicClass.objects.get_or_create(
        tenant=tenant,
        academic_level=acad_level,
        name="JSS 2 Gold"
    )
    curriculum, _ = Curriculum.objects.get_or_create(
        code="nat-curr",
        defaults={'name': "National Curriculum"}
    )
    subject, _ = Subject.objects.get_or_create(
        tenant=tenant,
        school=school,
        code="MATH101",
        defaults={
            'curriculum': curriculum,
            'name': "Mathematics"
        }
    )
    
    person, _ = Person.objects.get_or_create(
        tenant=tenant,
        person_number="PERS-DIRECT-001",
        defaults={
            'first_name': "Jane",
            'last_name': "Doe",
            'date_of_birth': timezone.now().date()
        }
    )
    student, _ = StudentProfile.objects.get_or_create(
        tenant=tenant,
        person=person,
        current_school=school,
        student_number="STD-DIRECT-001"
    )
    student.academic_class = class_from
    student.save()
    
    # 1. Test Gradebook grid & score saving
    grid = GradebookService.get_or_create_grid(
        academic_class=class_from,
        subject=subject,
        period=period,
        academic_year=year,
        tenant=tenant
    )
    assert len(grid) >= 1, "Gradebook grid initialization failed"
    entry = grid[0]

    updated = GradebookService.save_scores(
        entry_id=entry.id,
        ca_score=35,
        exam_score=50,
        is_absent=False,
        teacher_notes="Great performance"
    )
    assert updated.total_score == Decimal('85.00'), f"Total score mismatch: {updated.total_score}"
    assert updated.letter_grade == 'A', f"Letter grade mismatch: {updated.letter_grade}"
    print("[PASS] Gradebook score calculation & grade mapping verified.")

    # 2. Test Report Card compilation
    report = ReportCardService.compile_student_report_card(
        student=student,
        period=period,
        academic_year=year
    )
    assert report.total_score == Decimal('85.00'), f"Report card total mismatch: {report.total_score}"
    verified = ReportCardService.verify_qr_code(report.qr_verification_code)
    assert verified is not None and verified.id == report.id, "QR Code verification failed"
    print("[PASS] Report Card compilation & QR code verification verified.")

    # 3. Test Batch Promotion execution
    log = PromotionService.execute_batch_promotion(
        from_class=class_from,
        to_class=class_to,
        student_ids=[student.id],
        academic_year=year
    )
    assert log.promoted_count == 1, "Batch promotion log count mismatch"
    print("[PASS] Batch student promotion & audit log verified.")

    print("--- ALL ACADEMIC MODULE ENTERPRISE TESTS PASSED CLEANLY! ---")

if __name__ == "__main__":
    run_tests()
