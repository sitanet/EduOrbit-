from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from backend.apps.people.models import Person, StudentProfile
from backend.apps.portal.services.portals import ParentPortalService, StudentPortalService, StaffPortalService

class ParentDashboardAPIView(APIView):
    def get(self, request):
        parent_id = request.query_params.get('parent_id')
        try:
            parent = Person.objects.get(id=parent_id)
            res = ParentPortalService.get_parent_dashboard(parent_person=parent)
            return Response({"status": "success", "data": res}, status=status.HTTP_200_OK)
        except Person.DoesNotExist:
            return Response({"status": "error", "message": "Parent not found."}, status=status.HTTP_404_NOT_FOUND)


class StudentDashboardAPIView(APIView):
    def get(self, request):
        student_id = request.query_params.get('student_id')
        try:
            student = StudentProfile.objects.get(id=student_id)
            res = StudentPortalService.get_student_dashboard(student_profile=student)
            return Response({"status": "success", "data": res}, status=status.HTTP_200_OK)
        except StudentProfile.DoesNotExist:
            return Response({"status": "error", "message": "Student not found."}, status=status.HTTP_404_NOT_FOUND)


class StaffDashboardAPIView(APIView):
    def get(self, request):
        staff_id = request.query_params.get('staff_id')
        try:
            staff = Person.objects.get(id=staff_id)
            res = StaffPortalService.get_staff_dashboard(staff_person=staff)
            return Response({"status": "success", "data": res}, status=status.HTTP_200_OK)
        except Person.DoesNotExist:
            return Response({"status": "error", "message": "Staff person not found."}, status=status.HTTP_404_NOT_FOUND)


class PortalProfileAPIView(APIView):
    def get(self, request):
        person_id = request.query_params.get('person_id')
        try:
            person = Person.objects.get(id=person_id)
            return Response({
                "status": "success",
                "data": {
                    "person_number": person.person_number,
                    "first_name": person.first_name,
                    "last_name": person.last_name,
                    "gender": person.gender
                }
            }, status=status.HTTP_200_OK)
        except Person.DoesNotExist:
            return Response({"status": "error", "message": "Person not found."}, status=status.HTTP_404_NOT_FOUND)
