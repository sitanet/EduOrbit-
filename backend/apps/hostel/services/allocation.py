from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from backend.apps.hostel.models import HostelApplication, HostelBed, BedAllocation
from backend.apps.efbm.services.accounting import JournalPostingService
from backend.apps.core.services.notifications import UnifiedNotificationService

class HostelApplicationService:
    """
    Hostel Accommodation Application Engine.
    """
    @classmethod
    @transaction.atomic
    def submit_application(cls, student, hostel):
        tenant = student.tenant

        app = HostelApplication.objects.create(
            tenant=tenant,
            student=student,
            hostel=hostel,
            application_date=timezone.now().date(),
            status='pending'
        )

        UnifiedNotificationService.send_notification(
            recipient="Hostel Warden",
            title="Hostel Application Received",
            message=f"Student {student.person_number} applied for accommodation at {hostel.name}.",
            channels=['in_app', 'email']
        )

        return {
            "status": "success",
            "application_id": str(app.id),
            "student": student.person_number,
            "hostel": hostel.name,
            "application_status": app.status
        }


class RoomAllocationService:
    """
    Room & Bed Residential Allocation Engine with General Ledger Integration.
    """
    @classmethod
    @transaction.atomic
    def allocate_bed(cls, school, student, bed, term_fee=800.00):
        tenant = school.tenant
        fee = Decimal(str(term_fee))

        if bed.status != 'available':
            return {
                "status": "error",
                "message": f"Bed {bed.bed_number} in Room {bed.room.room_number} is not available (Current status: {bed.status})."
            }

        # 1. Mark Bed Occupied
        bed.status = 'occupied'
        bed.save()

        # 2. Create Bed Allocation Record
        allocation = BedAllocation.objects.create(
            tenant=tenant,
            bed=bed,
            student=student,
            start_date=timezone.now().date(),
            status='active'
        )

        # 3. Post General Ledger Accounting Entry (Debit Accounts Receivable Hostel, Credit Hostel Revenue)
        JournalPostingService.post_journal_entry(
            school=school,
            event_type="hostel_fee_billing",
            debit_account="Accounts Receivable (Hostel)",
            credit_account="Hostel Revenue",
            amount=fee
        )

        # 4. Dispatch Notification
        UnifiedNotificationService.send_notification(
            recipient=student.first_name,
            title="Hostel Bed Allocated",
            message=f"You have been allocated Bed {bed.bed_number} in Room {bed.room.room_number} ({bed.room.block.hostel.name}).",
            channels=['in_app', 'email']
        )

        return {
            "status": "success",
            "allocation_id": str(allocation.id),
            "student": student.person_number,
            "hostel": bed.room.block.hostel.name,
            "room_number": bed.room.room_number,
            "bed_number": bed.bed_number,
            "term_fee": float(fee)
        }


class OccupancyService:
    """
    Hostel Occupancy & Vacancy Analytics Service.
    """
    @classmethod
    def get_hostel_occupancy(cls, hostel):
        total_beds = HostelBed.objects.filter(room__block__hostel=hostel).count()
        occupied_beds = HostelBed.objects.filter(room__block__hostel=hostel, status='occupied').count()
        available_beds = total_beds - occupied_beds
        occupancy_pct = round((occupied_beds / total_beds * 100.0), 2) if total_beds > 0 else 0.0

        return {
            "hostel_name": hostel.name,
            "total_beds": total_beds,
            "occupied_beds": occupied_beds,
            "available_beds": available_beds,
            "occupancy_percentage": occupancy_pct
        }
