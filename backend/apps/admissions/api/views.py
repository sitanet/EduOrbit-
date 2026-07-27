from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction
from backend.apps.admissions.models import AdmissionApplication
from backend.apps.academic.models import AcademicYear, AcademicClass
from backend.apps.admissions.services import AdmissionConversionService

class ApplicationListAPIView(APIView):
    """
    List Admission Applications for current tenant.
    """
    def get(self, request):
        tenant = getattr(request, 'tenant', None)
        apps_qs = AdmissionApplication.objects.filter(tenant=tenant).select_related('applicant__person', 'intake__campaign')
        data = [
            {
                "id": str(a.id),
                "applicant_number": a.applicant.applicant_number,
                "applicant_name": f"{a.applicant.person.first_name} {a.applicant.person.last_name}",
                "intake": a.intake.name,
                "status": a.status,
                "application_date": a.application_date.isoformat()
            }
            for a in apps_qs
        ]
        return Response({"status": "success", "count": len(data), "data": data})

class ApplicantConversionAPIView(APIView):
    """
    One-click conversion of an applicant to an enrolled student.
    """
    @transaction.atomic
    def post(self, request):
        tenant = getattr(request, 'tenant', None)
        application_id = request.data.get('application_id')
        academic_year_id = request.data.get('academic_year_id')
        academic_class_id = request.data.get('academic_class_id')

        if not application_id or not academic_year_id or not academic_class_id:
            return Response({"status": "error", "message": "application_id, academic_year_id, and academic_class_id are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            application = AdmissionApplication.objects.get(id=application_id, tenant=tenant)
            academic_year = AcademicYear.objects.get(id=academic_year_id, tenant=tenant)
            academic_class = AcademicClass.objects.get(id=academic_class_id, tenant=tenant)

            res = AdmissionConversionService.convert_applicant_to_student(
                application=application,
                academic_year=academic_year,
                academic_class=academic_class
            )
            return Response({"status": "success", "message": "Applicant converted to student successfully.", "data": res}, status=status.HTTP_200_OK)
        except AdmissionApplication.DoesNotExist:
            return Response({"status": "error", "message": "Application not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
