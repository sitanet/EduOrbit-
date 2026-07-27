import os
import django
from datetime import date

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.config.settings.local")
django.setup()

from backend.apps.identity.models import User
from backend.apps.people.models import Person
from backend.apps.tenants.models import Tenant

def get_details():
    tenant = Tenant.objects.first()
    if not tenant:
        tenant = Tenant.objects.create(name="Grace High School Org")
        
    admin_user = User.objects.filter(is_superuser=True).first()
    if not admin_user:
        admin_user = User.objects.create_superuser(
            username="admin",
            email="admin@eduorbit.com",
            password="Password123!"
        )
        Person.objects.create(
            tenant=tenant,
            user=admin_user,
            first_name="System",
            last_name="Administrator",
            date_of_birth=date(1990, 1, 1)
        )
        print("Superuser created successfully!")
    else:
        admin_user.set_password("Password123!")
        admin_user.save()
        print("Superuser password verified/updated!")

    # Check for HR Officer / Staff User
    hr_user = User.objects.filter(username="hr_officer").first()
    if not hr_user:
        hr_user = User.objects.create_user(
            username="hr_officer",
            email="hr@eduorbit.com",
            password="Password123!",
            is_staff=True
        )
        Person.objects.create(
            tenant=tenant,
            user=hr_user,
            first_name="HR",
            last_name="Officer",
            date_of_birth=date(1992, 5, 15)
        )

    print("\n=======================================================")
    print("           EDUORBIT SYSTEM LOGIN CREDENTIALS           ")
    print("=======================================================")
    print("Tenant Name  : ", tenant.name)
    print("Tenant ID    : ", tenant.id)
    print("-------------------------------------------------------")
    print("1. SYSTEM ADMINISTRATOR (Superuser / HR Admin)")
    print("   Username  : admin")
    print("   Email     : admin@eduorbit.com")
    print("   Password  : Password123!")
    print("   Role      : IsHRAdmin / Superuser")
    print("-------------------------------------------------------")
    print("2. HR OFFICER (Staff / Manager)")
    print("   Username  : hr_officer")
    print("   Email     : hr@eduorbit.com")
    print("   Password  : Password123!")
    print("   Role      : IsHROfficer / Staff")
    print("=======================================================\n")

if __name__ == '__main__':
    get_details()
