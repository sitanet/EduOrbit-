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

    @staticmethod
    @transaction.atomic
    def create_employee_from_onboarding_draft(tenant, draft, actor_person=None):
        """
        Creates a complete employee record from an OnboardingDraft.
        Handles all 8 wizard steps (currently Steps 1-3 implemented, 4-8 use defaults).
        
        Args:
            tenant: Tenant instance
            draft: OnboardingDraft instance with completed wizard data
            actor_person: Person who approved the onboarding (for audit)
        
        Returns:
            EmployeeProfile instance
        
        Raises:
            ValidationError: If draft is incomplete or KYC verification missing
        """
        from backend.apps.hr.utils.encryption import StatutoryPIIEncryption
        from django.core.exceptions import ValidationError
        
        draft_data = draft.draft_data
        if not draft_data:
            raise ValidationError("Draft data is empty")
        
        # Ensure draft is marked completed
        draft.is_completed = True
        draft.save()
        
        # Extract Step 1: Personal & KYC
        step1 = draft_data.get('step1', {})
        first_name = step1.get('first_name', '').strip()
        middle_name = step1.get('middle_name', '').strip()
        last_name = step1.get('last_name', '').strip()
        dob = step1.get('dob')
        gender = step1.get('gender', 'other')
        marital_status = step1.get('marital_status', 'single')
        
        nin = step1.get('nin', '').strip()
        bvn = step1.get('bvn', '').strip()
        is_nin_verified = step1.get('nin_verified', False) or len(nin) >= 10
        is_bvn_verified = step1.get('bvn_verified', False) or len(bvn) >= 10
        kyc_meta = step1.get('kyc_meta', {})
        
        # Validate required demographics
        if not first_name or not last_name:
            raise ValidationError("First name and last name are required")
        if not dob:
            raise ValidationError("Date of birth is required")
        
        # Validate KYC (at least one must be verified or provided)
        if not is_nin_verified and not is_bvn_verified:
            raise ValidationError("Either NIN or BVN must be provided or verified before submission")
        
        # Extract Step 2: Employment
        step2 = draft_data.get('step2', {})
        job_title = step2.get('job_title', '').strip()
        department_name = step2.get('department', 'General')
        employment_type = step2.get('employment_type', 'full_time')
        employment_status = step2.get('employment_status', 'active')
        confirmation_status = step2.get('confirmation_status', 'probation')
        date_employed = step2.get('date_employed')
        probation_start = step2.get('probation_start_date')
        probation_end = step2.get('probation_end_date')
        campus_name = step2.get('campus', 'Main Campus')
        work_location = step2.get('work_location', '')
        cost_centre = step2.get('cost_centre', 'CC-101-ACADEMICS')
        division_name = step2.get('division', '')
        unit_name = step2.get('unit', '')
        
        if not job_title:
            raise ValidationError("Job title is required")
        if not date_employed:
            date_employed = timezone.now().date()
        
        # Extract Step 3: Banking & Statutory
        step3 = draft_data.get('step3', {})
        bank_name = step3.get('bank_name', '').strip()
        account_number = step3.get('account_number', '').strip()
        account_name = step3.get('account_name', '').strip()
        tax_id = step3.get('tax_id', '').strip()
        pfa_name = step3.get('pfa_name', '').strip()
        pension_number = step3.get('pension_number', '').strip()
        nhf_number = step3.get('nhf_number', '').strip()
        nhis_number = step3.get('nhis_number', '').strip()
        nsitf_number = step3.get('nsitf_number', '').strip()
        
        # Extract Step 4: Compensation (defaults for now)
        step4 = draft_data.get('step4', {})
        salary_grade = step4.get('salary_grade', 'grade_1')
        
        # Extract Step 5: Emergency Contacts (defaults for now)
        step5 = draft_data.get('step5', {})
        next_of_kin_name = step5.get('next_of_kin_name', '').strip()
        next_of_kin_relationship = step5.get('next_of_kin_relationship', '').strip()
        next_of_kin_phone = step5.get('next_of_kin_phone', '').strip()
        emergency_contact_phone = step5.get('emergency_contact_phone', '').strip()
        
        # Generate email if not provided
        email = step1.get('email', f"{first_name.lower()}.{last_name.lower()}@eduorbit.com")
        
        # Step 1: Check for duplicates BEFORE creating any records
        from backend.apps.hr.services.duplicate_detector import DuplicateDetectionService
        
        duplicate_check = DuplicateDetectionService.check_duplicates(
            tenant=tenant,
            email=email,
            nin=nin,
            bvn=bvn,
            account_number=account_number
        )
        
        if duplicate_check['has_duplicates']:
            # Raise validation error with all duplicate warnings
            error_message = "Duplicate employee data detected:\n" + "\n".join(duplicate_check['warnings'])
            raise ValidationError(error_message)
        
        # Step 2: Validate email uniqueness (existing validation)
        EmployeeValidator.validate_email_uniqueness(email, tenant)
        
        # Step 3: Create Person
        person = Person.objects.create(
            tenant=tenant,
            person_number=f"PER-{uuid.uuid4().hex[:6].upper()}",
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            gender=gender,
            date_of_birth=dob,
            marital_status=marital_status
        )
        
        # Step 4: Create Django User if missing
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
        
        # Step 5: Tenant Membership Role
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
        
        # Step 6: Add PersonRole
        school_obj = School.objects.filter(tenant=tenant).first()
        PersonRole.objects.get_or_create(
            tenant=tenant,
            person=person,
            role='staff',
            school=school_obj
        )
        
        # Step 7: Encrypt statutory PII
        nin_encrypted = StatutoryPIIEncryption.encode(nin) if nin else ""
        bvn_encrypted = StatutoryPIIEncryption.encode(bvn) if bvn else ""
        tax_id_encrypted = StatutoryPIIEncryption.encode(tax_id) if tax_id else ""
        rsa_pin_encrypted = StatutoryPIIEncryption.encode(pension_number) if pension_number else ""
        
        # Step 8: Create Employee Profile
        emp_num = f"EMP-{uuid.uuid4().hex[:6].upper()}"
        EmployeeValidator.validate_employee_number(emp_num, tenant)
        
        employee = EmployeeProfile.objects.create(
            tenant=tenant,
            person=person,
            employee_number=emp_num,
            job_title=job_title,
            salary_grade=salary_grade,
            status=employment_status,
            employment_type=employment_type,
            confirmation_status=confirmation_status,
            joined_date=date_employed,
            probation_end_date=probation_end,
            
            # Organizational
            campus_name=campus_name,
            department_name=department_name,
            division_name=division_name,
            unit_name=unit_name,
            cost_centre=cost_centre,
            
            # Banking
            bank_name=bank_name,
            account_number=account_number,
            account_name=account_name,
            
            # Statutory Encrypted
            nin_encrypted=nin_encrypted,
            bvn_encrypted=bvn_encrypted,
            tax_id_encrypted=tax_id_encrypted,
            rsa_pin_encrypted=rsa_pin_encrypted,
            
            # Statutory Plaintext
            pfa_name=pfa_name,
            nhf_number=nhf_number,
            nhis_number=nhis_number,
            nsitf_number=nsitf_number,
            
            # KYC Metadata
            is_nin_verified=is_nin_verified,
            is_bvn_verified=is_bvn_verified,
            kyc_verification_meta=kyc_meta,
            
            # Emergency
            next_of_kin_name=next_of_kin_name,
            next_of_kin_relationship=next_of_kin_relationship,
            next_of_kin_phone=next_of_kin_phone,
            emergency_contact_phone=emergency_contact_phone
        )
        
        # Step 8b: Process & Attach Photo if captured during onboarding
        try:
            photo_url = draft_data.get('photo_url') or draft_data.get('passport_photo') or draft_data.get('dojah_photo')
            photo_src = draft_data.get('photo_source') or ('DOJAH_NIN' if is_nin_verified else 'HR_UPLOAD')
            photo_ref = draft_data.get('photo_verification_reference') or nin or bvn or ""
            photo_reason = draft_data.get('photo_replacement_reason') or "Captured during HR Onboarding Wizard"

            if photo_url:
                from backend.apps.hr.services.photo_service import EmployeePhotoService
                EmployeePhotoService.replace_employee_photo(
                    employee=employee,
                    file_obj_or_bytes_or_url=photo_url,
                    source=photo_src,
                    provider="DOJAH" if "DOJAH" in photo_src else "HR_MANUAL",
                    method="NIN" if "NIN" in photo_src else ("BVN" if "BVN" in photo_src else "UPLOAD"),
                    ref=photo_ref,
                    actor_person=actor_person,
                    reason=photo_reason
                )
        except Exception as photo_err:
            import logging
            logging.getLogger(__name__).warning(f"Non-critical photo processing warning during employee creation: {photo_err}")

        # Step 9: StaffProfile
        StaffProfile.objects.get_or_create(
            tenant=tenant,
            person=person,
            employee_number=emp_num,
            defaults={'role_type': 'Support'}
        )
        
        # Step 10: Org Assignment
        OrgAssignmentHistory.objects.create(
            tenant=tenant,
            employee=employee,
            campus_name=campus_name,
            department_name=department_name,
            cost_centre=cost_centre,
            job_position=job_title,
            is_active=True
        )
        
        # Step 11: Seed Onboarding Tasks
        from backend.apps.hr.services.onboarding import OnboardingService
        OnboardingService.seed_default_tasks(tenant, employee)
        
        # Step 12: Audit Log
        HRAuditLog.objects.create(
            tenant=tenant,
            actor=actor_person,
            event_type='employee.onboarded',
            model_affected='EmployeeProfile',
            object_id=str(employee.id),
            new_values={
                'employee_number': emp_num,
                'email': email,
                'job_title': job_title,
                'draft_id': str(draft.draft_id),
                'created_from': 'onboarding_wizard'
            }
        )
        
        # Step 13: Mark draft as completed
        draft.is_completed = True
        draft.save()
        
        # Step 14: Publish Domain Event
        event = DomainEvent(
            "employee.onboarded",
            tenant_id=str(tenant.id),
            data={
                "id": str(employee.id),
                "employee_number": emp_num,
                "person_number": person.person_number,
                "username": user.username,
                "draft_id": str(draft.draft_id)
            }
        )
        transaction.on_commit(lambda: event_bus.publish(event))
        
        return employee
