from django.db import transaction
from backend.apps.academic.models import Subject, SubjectOffering, Curriculum

class AcademicCatalogService:
    """
    Curriculum & Academic Structure Catalog Service.
    Handles Subject catalog management, credit hours, and subject class offerings mapping.
    """
    @classmethod
    @transaction.atomic
    def create_subject(cls, school, curriculum, code, name, category='core', credit_units=3):
        tenant = school.tenant
        subject, created = Subject.objects.get_or_create(
            school=school,
            code=code,
            tenant=tenant,
            defaults={
                'curriculum': curriculum,
                'name': name,
                'category': category,
                'credit_units': credit_units,
                'is_active': True
            }
        )
        return {
            "status": "success",
            "created": created,
            "subject_id": str(subject.id),
            "code": subject.code,
            "name": subject.name,
            "credit_units": subject.credit_units
        }

    @classmethod
    @transaction.atomic
    def map_subject_to_class(cls, academic_year, subject, academic_class, compulsory=True, teacher_user_id=None):
        tenant = academic_class.tenant
        offering, created = SubjectOffering.objects.get_or_create(
            academic_year=academic_year,
            subject=subject,
            academic_class=academic_class,
            tenant=tenant,
            defaults={
                'compulsory': compulsory,
                'teacher_user_id': teacher_user_id
            }
        )
        return {
            "status": "success",
            "created": created,
            "offering_id": str(offering.id),
            "subject": subject.name,
            "academic_class": academic_class.name,
            "compulsory": offering.compulsory
        }

    @classmethod
    def get_class_curriculum_workload(cls, academic_class):
        offerings = SubjectOffering.objects.filter(academic_class=academic_class).select_related('subject')
        total_credits = sum(o.subject.credit_units for o in offerings)
        
        return {
            "academic_class": academic_class.name,
            "offering_count": len(offerings),
            "total_credit_units": total_credits,
            "subjects": [o.subject.name for o in offerings]
        }
