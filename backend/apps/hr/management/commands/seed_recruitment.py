import uuid
from django.core.management.base import BaseCommand
from django.utils import timezone
from backend.apps.tenants.models import Tenant, School
from backend.apps.hr.models import JobVacancy, JobApplication
from backend.apps.hr.services import RecruitmentService

class Command(BaseCommand):
    help = 'Seeds sample recruitment vacancies and candidate applications for testing.'

    def handle(self, *args, **options):
        tenant = Tenant.objects.first()
        if not tenant:
            tenant = Tenant.objects.create(name="Grace High School Org")
            
        vacancies = [
            ("Senior Physics Teacher", "Sciences", "Teach Senior Secondary Physics classes."),
            ("Head of Mathematics", "Mathematics", "Lead the Mathematics department."),
            ("School Guidance Counselor", "Administration", "Provide student counseling services.")
        ]
        
        for title, dept, desc in vacancies:
            vac, _ = JobVacancy.objects.get_or_create(
                tenant=tenant,
                title=title,
                defaults={'department': dept, 'description': desc, 'status': 'published'}
            )
            
            # Seed 2 candidates per vacancy
            RecruitmentService.submit_application(
                tenant=tenant,
                vacancy=vac,
                first_name="Alexander",
                last_name="Pierce",
                email=f"alexander.{uuid.uuid4().hex[:4]}@eduorbit.com",
                phone="+2348011223344"
            )
            RecruitmentService.submit_application(
                tenant=tenant,
                vacancy=vac,
                first_name="Carol",
                last_name="Danvers",
                email=f"carol.{uuid.uuid4().hex[:4]}@eduorbit.com",
                phone="+2348099887766"
            )

        self.stdout.write(self.style.SUCCESS("Successfully seeded recruitment vacancies and candidate applications!"))
