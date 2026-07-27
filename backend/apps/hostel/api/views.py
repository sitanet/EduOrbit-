from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from backend.apps.people.models import Person
from backend.apps.tenants.models import School
from backend.apps.hostel.models import Hostel, HostelBed, HostelApplication
from backend.apps.hostel.services.allocation import HostelApplicationService, RoomAllocationService, OccupancyService

class HostelListAPIView(APIView):
    def get(self, request):
        hostels = Hostel.objects.all()
        data = [
            {
                "id": str(h.id),
                "name": h.name,
                "gender": h.gender,
                "blocks_count": h.blocks.count()
            }
            for h in hostels
        ]
        return Response({"status": "success", "count": len(data), "data": data})


class HostelApplicationAPIView(APIView):
    def post(self, request):
        student_id = request.data.get('student_id')
        hostel_id = request.data.get('hostel_id')

        try:
            student = Person.objects.get(id=student_id)
            hostel = Hostel.objects.get(id=hostel_id)
            res = HostelApplicationService.submit_application(student=student, hostel=hostel)
            return Response({"status": "success", "data": res}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class RoomAllocateAPIView(APIView):
    def post(self, request):
        school_id = request.data.get('school_id')
        student_id = request.data.get('student_id')
        bed_id = request.data.get('bed_id')
        term_fee = request.data.get('term_fee', 800.00)

        try:
            school = School.objects.get(id=school_id)
            student = Person.objects.get(id=student_id)
            bed = HostelBed.objects.get(id=bed_id)
            res = RoomAllocationService.allocate_bed(school=school, student=student, bed=bed, term_fee=term_fee)
            return Response({"status": "success" if res["status"] == "success" else "error", "data": res}, status=status.HTTP_200_OK if res["status"] == "success" else status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class HostelOccupancyAPIView(APIView):
    def get(self, request):
        hostel_id = request.query_params.get('hostel_id')
        try:
            hostel = Hostel.objects.get(id=hostel_id)
            res = OccupancyService.get_hostel_occupancy(hostel=hostel)
            return Response({"status": "success", "data": res}, status=status.HTTP_200_OK)
        except Hostel.DoesNotExist:
            return Response({"status": "error", "message": "Hostel not found."}, status=status.HTTP_404_NOT_FOUND)
