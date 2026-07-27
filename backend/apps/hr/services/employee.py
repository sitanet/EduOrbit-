import uuid
from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from backend.apps.people.models import Person, StaffProfile, PersonRole
from backend.apps.identity.models import User, Role, TenantMembership
from backend.apps.tenants.models import School
from backend.apps.hr.models import EmployeeProfile, OrgAssignmentHistory, HRAuditLog
from backend.apps.hr.validators import EmployeeValidator
from backend.apps.core.events import event_bus, DomainEvent

class EmployeeService:
    @staticmethod
    @transaction.atomic
    def create_employee(tenant, first_name, last_name, email, job_title, salary_grade='grade_1', employment_type='full_time', school=None, department_name='Academics'):
        EmployeeValidator.validate_email_uniqueness(email, tenant)
        
        # 1. Find or create Person
        person = Person.objects.filter(tenant=tenant, user__email=email).first()
        if not person:
            person = Person.objects.create(
                tenant=tenant,
                person_number=f"PER-{uuid.uuid4().hex[:6].upper()}",
                first_name=first_name,
                last_name=last_name,
                gender='other',
                date_of_birth=timezone.now().date()
            )
            
        # 2. Create Django User if missing
        if not person.user:
            username = f"{first_name.lower()}.{last_name.lower()}"
            counter = 1
            base_username = username
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
                
            user = User.objects.create_user(
                username=username,
                email=email,
                password="ChangeMe123!"
            )
            person.user = user
            person.save()
        else:
            user = person.user
            
        # 3. Tenant Membership Role
        r_code = f"staff_{tenant.id.hex[:8]}"
        role_obj, _ = Role.objects.get_or_create(
            tenant=tenant,
            code=r_code,
            defaults={'name': 'Staff'}
        )
        TenantMembership.objects.get_or_create(
            user=user,
            tenant=tenant,
            role=role_obj
        )
        
        # 4. Add PersonRole
        school_obj = school or School.objects.filter(tenant=tenant).first()
        PersonRole.objects.get_or_create(
            tenant=tenant,
            person=person,
            role='staff',
            school=school_obj
        )
        
        # 5. Create Employee Profile
        emp_num = f"EMP-{uuid.uuid4().hex[:6].upper()}"
        EmployeeValidator.validate_employee_number(emp_num, tenant)
        
        employee = EmployeeProfile.objects.create(
            tenant=tenant,
            person=person,
            employee_number=emp_num,
            job_title=job_title,
            salary_grade=salary_grade,
            employment_type=employment_type,
            confirmation_status='probation',
            status='active'
        )
        
        StaffProfile.objects.get_or_create(
            tenant=tenant,
            person=person,
            employee_number=emp_num,
            defaults={'role_type': 'Support'}
        )
        
        # 6. Org Assignment
        OrgAssignmentHistory.objects.create(
            tenant=tenant,
            employee=employee,
            campus_name=school_obj.name if school_obj else 'Grace Main Campus',
            department_name=department_name,
            job_position=job_title,
            is_active=True
        )
        
        # 7. Audit Log & Domain Event
        HRAuditLog.objects.create(
            tenant=tenant,
            actor=person,
            event_type='employee.created',
            model_affected='EmployeeProfile',
            object_id=str(employee.id),
            new_values={'employee_number': emp_num, 'email': email, 'job_title': job_title}
        )
        
        event = DomainEvent("employee.created", tenant_id=str(tenant.id), data={"id": str(employee.id), "employee_number": emp_num})
        transaction.on_commit(lambda: event_bus.publish(event))
        
        return employee

    @staticmethod
    @transaction.atomic
    def update_employee(tenant, employee_id, actor_person=None, **fields):
        employee = EmployeeProfile.objects.get(tenant=tenant, id=employee_id)
        old_data = {'status': employee.status, 'job_title': employee.job_title, 'salary_grade': employee.salary_grade}
        
        for key, value in fields.items():
            if hasattr(employee, key):
                setattr(employee, key, value)
                
        employee.save()
        
        HRAuditLog.objects.create(
            tenant=tenant,
            actor=actor_person,
            event_type='employee.updated',
            model_affected='EmployeeProfile',
            object_id=str(employee.id),
            old_values=old_data,
            new_values=fields
        )
        
        event = DomainEvent("employee.updated", tenant_id=str(tenant.id), data={"id": str(employee.id)})
        transaction.on_commit(lambda: event_bus.publish(event))
        return employee

    @staticmethod
    @transaction.atomic
    def transition_status(tenant, employee_id, new_status, actor_person=None, reason=""):
        employee = EmployeeProfile.objects.get(tenant=tenant, id=employee_id)
        old_status = employee.status
        employee.status = new_status
        if new_status == 'confirmed':
            employee.confirmation_status = 'confirmed'
        employee.save()
        
        HRAuditLog.objects.create(
            tenant=tenant,
            actor=actor_person,
            event_type=f'employee.status_changed.{new_status}',
            model_affected='EmployeeProfile',
            object_id=str(employee.id),
            old_values={'status': old_status},
            new_values={'status': new_status},
            reason=reason
        )
        
        if new_status in ['exited', 'archived', 'suspended']:
            event = DomainEvent("employee.terminated", tenant_id=str(tenant.id), data={"id": str(employee.id), "status": new_status})
            transaction.on_commit(lambda: event_bus.publish(event))
            
        return employee
