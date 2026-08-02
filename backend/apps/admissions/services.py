from django.db import transaction
from backend.apps.people.models import StudentProfile
from backend.apps.students.models import StudentStatusHistory, AcademicPlacementHistory
from backend.apps.students.services.student_number import StudentNumberGeneratorService
from backend.apps.admissions.models import AdmissionApplication, AdmissionOffer
from backend.apps.core.services.notifications import UnifiedNotificationService

class AdmissionConversionService:
    """
    Service for 1-click conversion of an accepted Applicant into an enrolled Student.
    Executes atomically inside transaction.atomic().
    """
    @classmethod
    @transaction.atomic
    def convert_applicant_to_student(cls, application, academic_year, academic_class, house=None):
        if application.status not in ['accepted', 'offered', 'submitted']:
            # Allow conversion for accepted or submitted applications
            pass

        person = application.applicant.person
        tenant = application.tenant

        # 1. Generate Student ID
        student_number = StudentNumberGeneratorService.generate_next_student_number(tenant=tenant)
        admission_number = f"ADM-{student_number.split('-')[-1]}"

        # 2. Create StudentProfile
        student_profile, created = StudentProfile.objects.get_or_create(
            person=person,
            tenant=tenant,
            defaults={
                'student_number': student_number,
                'admission_number': admission_number,
                'current_school': application.intake.campaign.school,
                'enrollment_status': 'active'
            }
        )

        # 3. Create AcademicPlacementHistory
        placement = AcademicPlacementHistory.objects.create(
            tenant=tenant,
            student=student_profile,
            academic_year=academic_year,
            academic_class=academic_class,
            house=house,
            campus=academic_class.academic_level.education_level.school.campuses.first() if hasattr(academic_class.academic_level.education_level.school, 'campuses') else None
        )

        # 4. Record StudentStatusHistory
        status_history = StudentStatusHistory.objects.create(
            tenant=tenant,
            student=student_profile,
            status='active',
            reason=f"Converted from Admission Application #{application.id}"
        )

        # 5. Update Application Status
        application.status = 'enrolled'
        application.save()

        # 6. Dispatch Unified Notification
        UnifiedNotificationService.send_notification(
            recipient=person.first_name,
            title="Admission Conversion Complete",
            message=f"Welcome to {application.intake.campaign.school.name}! Your Student ID is {student_number}.",
            channels=['in_app', 'email']
        )

        return {
            "status": "success",
            "student_profile_id": str(student_profile.id),
            "student_number": student_profile.student_number,
            "admission_number": student_profile.admission_number,
            "placement_id": str(placement.id),
            "status_history_id": str(status_history.id)
        }


class EnrollmentService:
    @classmethod
    @transaction.atomic
    def enroll_applicant(cls, application_id, class_id):
        from backend.apps.admissions.models import AdmissionApplication
        from backend.apps.academic.models import AcademicClass
        from backend.apps.people.models import StudentProfile, PersonRole
        
        application = AdmissionApplication.objects.get(id=application_id)
        ac_class = AcademicClass.objects.get(id=class_id)
        tenant = application.tenant
        school = application.intake.campaign.school
        
        # 1. Update application status
        application.status = 'enrolled'
        application.save()
        
        # 2. Get or create StudentProfile
        student_profile, created = StudentProfile.objects.get_or_create(
            person=application.applicant.person,
            tenant=tenant,
            defaults={
                'student_number': f"STU-{application.applicant.person.person_number.split('-')[-1]}",
                'admission_number': f"ADM-{application.applicant.person.person_number.split('-')[-1]}",
                'current_school': school,
                'enrollment_status': 'enrolled'
            }
        )
        if student_profile.enrollment_status != 'enrolled':
            student_profile.enrollment_status = 'enrolled'
            student_profile.save()
            
        # 3. Assign PersonRole with role='student', school is required (non-nullable FK)
        PersonRole.objects.get_or_create(
            tenant=tenant,
            person=application.applicant.person,
            role='student',
            school=school
        )
        
        return student_profile

