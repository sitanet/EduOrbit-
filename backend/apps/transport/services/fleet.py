from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from backend.apps.transport.models import Vehicle, VehicleCategory, Driver, Route, RouteStop, Trip, TripPassenger, TransportSubscription
from backend.apps.efbm.services.accounting import JournalPostingService
from backend.apps.core.services.notifications import UnifiedNotificationService

class FleetService:
    """
    Vehicle Fleet Management Engine.
    """
    @classmethod
    @transaction.atomic
    def register_vehicle(cls, school, category, registration_number, plate_number, capacity=30):
        tenant = school.tenant

        vehicle = Vehicle.objects.create(
            tenant=tenant,
            category=category,
            registration_number=registration_number,
            plate_number=plate_number,
            capacity=capacity,
            status='active'
        )

        return {
            "status": "success",
            "vehicle_id": str(vehicle.id),
            "registration_number": vehicle.registration_number,
            "plate_number": vehicle.plate_number,
            "capacity": vehicle.capacity
        }


class RouteService:
    """
    Bus Route & Stops Optimization Engine.
    """
    @classmethod
    @transaction.atomic
    def create_route(cls, school, name, start_point, end_point, distance_km=10.00):
        tenant = school.tenant

        route = Route.objects.create(
            tenant=tenant,
            name=name,
            start_point=start_point,
            end_point=end_point,
            total_distance_km=Decimal(str(distance_km))
        )

        return {
            "status": "success",
            "route_id": str(route.id),
            "name": route.name,
            "distance_km": float(route.total_distance_km)
        }

    @classmethod
    @transaction.atomic
    def add_stop(cls, route, stop_name, stop_order=1):
        stop = RouteStop.objects.create(
            tenant=route.tenant,
            route=route,
            stop_name=stop_name,
            stop_order=stop_order
        )

        return {
            "status": "success",
            "stop_id": str(stop.id),
            "route_name": route.name,
            "stop_name": stop.stop_name,
            "stop_order": stop.stop_order
        }


class TransportAttendanceService:
    """
    Bus Passenger Boarding & Attendance Check-In Engine with Real-Time Parent Alerts.
    """
    @classmethod
    @transaction.atomic
    def check_in_student(cls, trip, student):
        tenant = trip.tenant

        passenger, _ = TripPassenger.objects.get_or_create(
            tenant=tenant,
            trip=trip,
            student=student,
            defaults={'status': 'boarded', 'boarded_time': timezone.now()}
        )

        passenger.status = 'boarded'
        passenger.boarded_time = timezone.now()
        passenger.save()

        # Real-time parent notification alert
        UnifiedNotificationService.send_notification(
            recipient=student.first_name,
            title="Bus Boarding Notification",
            message=f"Student {student.person_number} has boarded the bus on Route '{trip.route.name}'.",
            channels=['in_app', 'email']
        )

        return {
            "status": "success",
            "passenger_id": str(passenger.id),
            "student_number": student.person_number,
            "route_name": trip.route.name,
            "boarded_time": str(passenger.boarded_time),
            "status_name": passenger.status
        }


class TransportFeeService:
    """
    Transport Billing Engine with General Ledger Accounting Integration.
    """
    @classmethod
    @transaction.atomic
    def generate_transport_fee(cls, school, student, route, term_fee=300.00):
        tenant = school.tenant
        fee = Decimal(str(term_fee))

        # GL Journal Entry (Debit Accounts Receivable Transport, Credit Transport Revenue)
        JournalPostingService.post_journal_entry(
            school=school,
            event_type="transport_fee_billing",
            debit_account="Accounts Receivable (Transport)",
            credit_account="Transport Fare Revenue",
            amount=fee
        )

        return {
            "status": "success",
            "student_number": student.person_number,
            "route_name": route.name,
            "term_fee": float(fee)
        }
