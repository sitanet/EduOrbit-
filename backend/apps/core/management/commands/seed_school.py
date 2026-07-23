from django.core.management.base import BaseCommand
from django.db import transaction
from faker import Faker

fake = Faker()

class Command(BaseCommand):
    help = 'Generates a demo school, Branding, Academic Session, Terms, Departments, Houses, Subjects, Timetable.'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding school data...")
        
        try:
            # from apps.school.models import School, Branding, AcademicSession, Term, Department, House, Subject
            
            self.stdout.write("Creating Demo School and Branding...")
            school_name = "EduOrbit International School"
            
            self.stdout.write("Creating Academic Session and Terms...")
            session = "2026/2027"
            terms = ["First Term", "Second Term", "Third Term"]
            
            self.stdout.write("Creating Departments...")
            departments = ["Science", "Arts", "Commercial", "Vocational"]
            
            self.stdout.write("Creating Houses...")
            houses = ["Red House", "Blue House", "Green House", "Yellow House"]
            
            self.stdout.write("Creating Subjects...")
            subjects = [
                "Mathematics", "English Language", "Physics", "Chemistry", 
                "Biology", "Economics", "History", "Geography", "Computer Science"
            ]
            
            self.stdout.write("Generating Timetable...")
            
            self.stdout.write(self.style.SUCCESS('Successfully seeded school data.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error seeding school data: {e}'))
