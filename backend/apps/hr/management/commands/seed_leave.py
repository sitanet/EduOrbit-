import uuid
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from backend.apps.tenants.models import Tenant
from backend.apps.hr.models import LeaveType, LeaveBalance, EmployeeProfile
from backend.apps.hr.services import LeaveService

class Command(BaseCommand):
    help = 'Seeds default leave types, employee balances, and leave requests for testing.'

    def handle(self, *args, **options):
        tenant = Tenant.objects.first()
        if not tenant:
            tenant = Tenant.objects.create(name="Grace High School Org")
            
        leave_types = [
            ("Annual Leave", "AL", 20, True, False, True),
            ("Sick Leave", "SL", 10, True, True, False),
            ("Maternity Leave", "ML", 90, True, True, False),
            ("Paternity Leave", "PL", 10, True, False, False),
            ("Study Leave", "STL", 14, False, True, False),
        ]
        
        created_types = []
        for name, code, days, is_paid, req_doc, encash in leave_types:
            lt, _ = LeaveType.objects.get_or_create(
                tenant=tenant,
                code=code,
                defaults={
                    'name': name,
                    'default_days_per_year': days,
                    'is_paid': is_paid,
                    'requires_document': req_doc,
                    'allow_encashment': encash
                }
            )
            created_types.append(lt)
            
        employees = EmployeeProfile.objects.filter(tenant=tenant)
        al_type = created_types[0]
        
        for emp in employees:
            LeaveBalance.objects.get_or_create(
                tenant=tenant,
                employee=emp,
                leave_type=al_type,
                defaults={
                    'leave_type_name': al_type.name,
                    'allowed_days': al_type.default_days_per_year,
                    'remaining_days': al_type.default_days_per_year
                }
            )
            
        # Seed 1 leave request
        emp0 = employees.first()
        if emp0:
            start_date = timezone.now().date() + timedelta(days=5)
            end_date = start_date + timedelta(days=3)
            LeaveService.submit_leave_request(
                tenant=tenant,
                employee=emp0,
                leave_type=al_type,
                start_date=start_date,
                end_date=end_date,
                reason="Annual vacation"
            )

        self.stdout.write(self.style.SUCCESS("Successfully seeded default leave types, balances, and leave requests!"))
