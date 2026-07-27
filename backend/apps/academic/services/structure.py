from django.db import transaction
from backend.apps.academic.models import AcademicYear, AcademicPeriod

class AcademicStructureService:
    """
    Service Layer for managing Academic Years, Academic Terms/Periods, and Term Rollover.
    """
    @classmethod
    @transaction.atomic
    def activate_academic_year(cls, academic_year):
        """
        Activates the target AcademicYear while archiving previous active years for the school.
        """
        school = academic_year.school
        
        # Deactivate current active years
        AcademicYear.objects.filter(school=school, status='active').update(status='archived')
        
        # Activate target year
        academic_year.status = 'active'
        academic_year.save()
        
        return {
            "status": "success",
            "active_year": academic_year.name,
            "academic_year_id": str(academic_year.id)
        }

    @classmethod
    @transaction.atomic
    def activate_academic_period(cls, academic_period):
        """
        Activates a specific term/semester while marking others in the same academic year as completed or future.
        """
        academic_year = academic_period.academic_year
        
        # Complete currently active periods under this year
        AcademicPeriod.objects.filter(academic_year=academic_year, status='active').update(status='completed')
        
        academic_period.status = 'active'
        academic_period.save()
        
        return {
            "status": "success",
            "active_period": academic_period.name,
            "academic_period_id": str(academic_period.id)
        }
