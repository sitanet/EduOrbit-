from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from backend.apps.tenants.models import School
from backend.apps.people.models import Person
from backend.apps.transport.models import Route, Vehicle, Trip
from backend.apps.transport.services.fleet import TransportAttendanceService, TransportFeeService

class RouteListAPIView(APIView):
    def get(self, request):
        routes = Route.objects.all()
        data = [
            {
                "id": str(r.id),
                "name": r.name,
                "start_point": r.start_point,
                "end_point": r.end_point,
                "distance_km": float(r.total_distance_km),
                "stops_count": r.stops.count()
            }
            for r in routes
        ]
        return Response({"status": "success", "count": len(data), "data": data})


class VehicleListAPIView(APIView):
    def get(self, request):
        vehicles = Vehicle.objects.all()
        data = [
            {
                "id": str(v.id),
                "registration_number": v.registration_number,
                "plate_number": v.plate_number,
                "capacity": v.capacity,
                "status": v.status
            }
            for v in vehicles
        ]
        return Response({"status": "success", "count": len(data), "data": data})


class StudentCheckInAPIView(APIView):
    def post(self, request):
        trip_id = request.data.get('trip_id')
        student_id = request.data.get('student_id')

        try:
            trip = Trip.objects.get(id=trip_id)
            student = Person.objects.get(id=student_id)
            res = TransportAttendanceService.check_in_student(trip=trip, student=student)
            return Response({"status": "success", "data": res}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class TransportPaymentAPIView(APIView):
    def post(self, request):
        school_id = request.data.get('school_id')
        student_id = request.data.get('student_id')
        route_id = request.data.get('route_id')
        term_fee = request.data.get('term_fee', 300.00)

        try:
            school = School.objects.get(id=school_id)
            student = Person.objects.get(id=student_id)
            route = Route.objects.get(id=route_id)
            res = TransportFeeService.generate_transport_fee(school=school, student=student, route=route, term_fee=term_fee)
            return Response({"status": "success", "data": res}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
