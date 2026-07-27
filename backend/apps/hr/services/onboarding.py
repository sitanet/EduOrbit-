from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from backend.apps.hr.models import OnboardingTask
from backend.apps.core.events import event_bus, DomainEvent

class OnboardingService:
    @staticmethod
    @transaction.atomic
    def seed_default_tasks(tenant, employee):
        tasks = [
            ('Submit signed employment contract', 'contract'),
            ('Identity verification and capturing', 'identity'),
            ('Background reference check', 'background'),
            ('Medical clearance report submission', 'medical'),
            ('Compliance and safety policy signoff', 'policy')
        ]
        created_tasks = []
        for t_name, cat in tasks:
            t, _ = OnboardingTask.objects.get_or_create(
                tenant=tenant,
                employee=employee,
                task_name=t_name,
                category=cat,
                defaults={'due_date': timezone.now().date() + timedelta(days=7)}
            )
            created_tasks.append(t)
        return created_tasks

    @staticmethod
    @transaction.atomic
    def toggle_task(tenant, task_id, is_completed=True, verifier_employee=None):
        task = OnboardingTask.objects.get(tenant=tenant, id=task_id)
        task.is_completed = is_completed
        task.completed_at = timezone.now() if is_completed else None
        if verifier_employee:
            task.verified_by = verifier_employee
        task.save()
        
        # Check if all tasks completed for employee
        remaining = OnboardingTask.objects.filter(tenant=tenant, employee=task.employee, is_completed=False).count()
        if remaining == 0:
            event = DomainEvent("onboarding.completed", tenant_id=str(tenant.id), data={"employee_id": str(task.employee.id)})
            transaction.on_commit(lambda: event_bus.publish(event))
            
        return task
