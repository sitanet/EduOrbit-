import os
import django
import sys
from datetime import date
from django.utils import timezone

# Set django env
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
django.setup()

from backend.apps.tenants.models import Tenant, School
from backend.apps.people.models import Person, StudentProfile
from backend.apps.students.models import StudentPortfolio, StudentTimeline

def seed():
    tenant = Tenant.objects.first()
    school = School.objects.first()
    
    if not tenant or not school:
        print("No tenant or school found. Please onboard first.")
        return
        
    print(f"Seeding under tenant '{tenant.name}', school '{school.name}'...")
    
    # 1. Create John Doe Person
    john_person, _ = Person.objects.get_or_create(
        person_number="PER-0001",
        tenant=tenant,
        defaults={
            "first_name": "John",
            "last_name": "Doe",
            "gender": "male",
            "date_of_birth": date(2010, 5, 12),
        }
    )
    
    # Create John Doe Student
    john_student, _ = StudentProfile.objects.get_or_create(
        student_number="STU-2026-0004",
        tenant=tenant,
        defaults={
            "person": john_person,
            "current_school": school,
            "enrollment_status": "enrolled",
        }
    )
    
    # 2. Create Alice Smith Person
    alice_person, _ = Person.objects.get_or_create(
        person_number="PER-0002",
        tenant=tenant,
        defaults={
            "first_name": "Alice",
            "last_name": "Smith",
            "gender": "female",
            "date_of_birth": date(2011, 8, 20),
        }
    )
    
    # Create Alice Smith Student
    alice_student, _ = StudentProfile.objects.get_or_create(
        student_number="STU-2026-0012",
        tenant=tenant,
        defaults={
            "person": alice_person,
            "current_school": school,
            "enrollment_status": "enrolled",
        }
    )
    
    # 3. Create Portfolios
    StudentPortfolio.objects.get_or_create(
        student=john_student,
        tenant=tenant,
        title="Best Science Project Award",
        defaults={
            "description": "Developed a solar powered water filtration model.",
            "date_earned": date(2026, 7, 15)
        }
    )
    
    StudentPortfolio.objects.get_or_create(
        student=alice_student,
        tenant=tenant,
        title="National Debate Championship",
        defaults={
            "description": "Placed 1st runner up in regional inter-school debate.",
            "date_earned": date(2026, 6, 20)
        }
    )
    
    # 4. Create Timelines
    StudentTimeline.objects.get_or_create(
        student=john_student,
        tenant=tenant,
        event_type="achievement",
        title="Awarded: Best Science Project Award",
        defaults={
            "description": "Developed a solar powered water filtration model.",
            "occurred_at": timezone.now()
        }
    )
    
    StudentTimeline.objects.get_or_create(
        student=alice_student,
        tenant=tenant,
        event_type="achievement",
        title="Awarded: National Debate Championship",
        defaults={
            "description": "Placed 1st runner up in regional inter-school debate.",
            "occurred_at": timezone.now()
        }
    )
    
    print("Seeding completed successfully!")

if __name__ == '__main__':
    seed()
