from decimal import Decimal
from backend.apps.portal.models import ParentStudentRelationship, PortalAnnouncement
from backend.apps.efbm.models import StudentWallet, Invoice
from backend.apps.library.models import BookIssue
from backend.apps.hostel.models import BedAllocation
from backend.apps.people.models import StudentProfile

class ParentPortalService:
    """
    Parent Self-Service Portal Aggregator Engine.
    Consumes existing Finance, Academic, Library, and Hostel services.
    """
    @classmethod
    def get_parent_dashboard(cls, parent_person):
        rels = ParentStudentRelationship.objects.filter(parent=parent_person)
        children = [r.student for r in rels]

        children_summary = []
        for child in children:
            wallet = StudentWallet.objects.filter(student=child).first()
            invoices = Invoice.objects.filter(student=child, status='issued')
            unpaid_balance = sum(inv.items.aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00') for inv in invoices) if hasattr(invoices, 'items') else Decimal('0.00')
            
            loans_count = BookIssue.objects.filter(borrower=child.person, status='issued').count()
            bed_alloc = BedAllocation.objects.filter(student=child.person, status='active').first()

            children_summary.append({
                "student_number": child.student_number,
                "first_name": child.person.first_name,
                "last_name": child.person.last_name,
                "wallet_balance": float(wallet.balance) if wallet else 0.00,
                "borrowed_books_count": loans_count,
                "hostel_room": bed_alloc.bed.room.room_number if bed_alloc else "Day Student"
            })

        announcements = PortalAnnouncement.objects.filter(target_role='parent')

        return {
            "parent_name": f"{parent_person.first_name} {parent_person.last_name}",
            "total_children": len(children_summary),
            "children": children_summary,
            "announcements": [{"title": a.title, "body": a.body} for a in announcements]
        }


class StudentPortalService:
    """
    Student Self-Service Portal Aggregator Engine.
    """
    @classmethod
    def get_student_dashboard(cls, student_profile):
        wallet = StudentWallet.objects.filter(student=student_profile).first()
        loans = BookIssue.objects.filter(borrower=student_profile.person, status='issued')
        bed_alloc = BedAllocation.objects.filter(student=student_profile.person, status='active').first()

        return {
            "student_number": student_profile.student_number,
            "full_name": f"{student_profile.person.first_name} {student_profile.person.last_name}",
            "school_name": student_profile.current_school.name if student_profile.current_school else "N/A",
            "wallet_balance": float(wallet.balance) if wallet else 0.00,
            "active_borrowed_books": [
                {
                    "barcode": l.copy.barcode,
                    "title": l.copy.book.title,
                    "due_date": str(l.due_date)
                }
                for l in loans
            ],
            "hostel_allocation": {
                "hostel": bed_alloc.bed.room.block.hostel.name if bed_alloc else "None",
                "room": bed_alloc.bed.room.room_number if bed_alloc else "N/A",
                "bed": bed_alloc.bed.bed_number if bed_alloc else "N/A"
            }
        }


class StaffPortalService:
    """
    Staff Self-Service Portal Aggregator Engine.
    """
    @classmethod
    def get_staff_dashboard(cls, staff_person):
        return {
            "staff_id": staff_person.person_number,
            "full_name": f"{staff_person.first_name} {staff_person.last_name}",
            "gender": staff_person.gender,
            "date_joined": str(staff_person.created_at.date()) if hasattr(staff_person, 'created_at') else "N/A",
            "status": "Active Staff"
        }
