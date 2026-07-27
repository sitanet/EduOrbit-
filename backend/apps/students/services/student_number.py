from django.utils import timezone
from backend.apps.people.models import StudentProfile

class StudentNumberGeneratorService:
    """
    Configurable Pattern-based Student ID Generator Service.
    Default Pattern: STU-{YEAR}-{SEQ:5} (e.g. STU-2026-00001)
    """
    @classmethod
    def generate_next_student_number(cls, tenant=None, prefix="STU"):
        current_year = timezone.now().strftime("%Y")
        
        # Count existing students for current tenant & year
        qs = StudentProfile.objects.all()
        if tenant:
            qs = qs.filter(tenant=tenant)
            
        latest_count = qs.filter(student_number__icontains=current_year).count() + 1
        candidate = f"{prefix}-{current_year}-{str(latest_count).zfill(5)}"
        while StudentProfile.objects.filter(student_number=candidate).exists():
            latest_count += 1
            candidate = f"{prefix}-{current_year}-{str(latest_count).zfill(5)}"

        return candidate
