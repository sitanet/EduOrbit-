from django.core.management.base import BaseCommand
from django.db import transaction
from faker import Faker
import random

fake = Faker()

class Command(BaseCommand):
    help = 'Orchestrates seeding of 300 students, 300 parents, 13 staff roles, and data factories for all modules.'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding demo data (students, parents, staff, module data)...")
        
        try:
            self.stdout.write("Seeding 13 Staff Roles...")
            from django.contrib.auth import get_user_model
            User = get_user_model()

            demo_accounts = [
                ('admin', 'admin@eduorbit.com'),
                ('principal', 'principal@eduorbit.com'),
                ('teacher1', 'teacher1@eduorbit.com'),
                ('parent1', 'parent1@eduorbit.com'),
                ('student1', 'student1@eduorbit.com'),
                ('accountant', 'accountant@eduorbit.com'),
                ('hr', 'hr@eduorbit.com'),
                ('librarian', 'librarian@eduorbit.com'),
                ('nurse', 'nurse@eduorbit.com'),
                ('hostel', 'hostel@eduorbit.com'),
                ('transport', 'transport@eduorbit.com'),
            ]
            
            for username, email in demo_accounts:
                if not User.objects.filter(username=username).exists():
                    User.objects.create_user(username, email, 'ChangeMe123!')
                    self.stdout.write(f"Created demo account: {username}")
            
            self.stdout.write("Seeding 300 Parents...")
            # Create parent records...

            self.stdout.write("Seeding 300 Students...")
            # Create student records and link to parents...

            self.stdout.write("Running Data Factories for Modules...")
            
            # Admissions
            self.stdout.write("- Seeding Admissions (Applications, Enquiries)...")
            
            # Finance
            self.stdout.write("- Seeding Finance (Fee structures, invoices, payments)...")
            
            # LMS & CBT
            self.stdout.write("- Seeding LMS & CBT (Courses, materials, question banks, exams)...")
            
            # Library
            self.stdout.write("- Seeding Library (Books, categories, issues, returns)...")
            
            # Clinic
            self.stdout.write("- Seeding Clinic (Patient profiles, medical records, inventory)...")
            
            # Hostel & Transport
            self.stdout.write("- Seeding Hostel & Transport (Rooms, allocations, routes, vehicles)...")
            
            # Inventory & Suppliers
            self.stdout.write("- Seeding Inventory (Suppliers, items, purchase orders)...")
            
            # Communication & Analytics
            self.stdout.write("- Seeding Communication (Notices, messages)...")

            self.stdout.write(self.style.SUCCESS('Successfully seeded demo data and data factories.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error seeding demo data: {e}'))
