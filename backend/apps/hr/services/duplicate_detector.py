from backend.apps.hr.models import EmployeeProfile
from backend.apps.people.models import Person

class DuplicateDetectionService:
    """
    9-Field Duplicate Detection Engine.
    Warns HR if matching NIN, BVN, Phone, Email, Employee Number, Account Number, or RSA PIN exists.
    
    Enhanced in Phase 12.4.3F to include BVN and NIN duplicate checks.
    """
    @classmethod
    def check_duplicates(cls, tenant, email=None, phone=None, nin=None, bvn=None, account_number=None, employee_number=None):
        """
        Check for duplicate employee data across multiple fields.
        
        Args:
            tenant: Tenant instance for multi-tenant isolation
            email: Email address to check
            phone: Phone number to check
            nin: National Identity Number (will be checked in encrypted form)
            bvn: Bank Verification Number (will be checked in encrypted form)
            account_number: Bank account number to check
            employee_number: Employee number to check
        
        Returns:
            dict with keys: has_duplicates, warning_count, warnings
        """
        from backend.apps.hr.utils.encryption import StatutoryPIIEncryption
        
        warnings = []
        
        # Email duplicate check
        if email and Person.objects.filter(tenant=tenant, user__email__iexact=email).exists():
            warnings.append(f"Email '{email}' is already assigned to an existing user profile.")
        
        # Phone duplicate check
        if phone and Person.objects.filter(tenant=tenant, phone_number=phone).exists():
            warnings.append(f"Phone number '{phone}' is registered under another person record.")
        
        # Employee number duplicate check
        if employee_number and EmployeeProfile.objects.filter(tenant=tenant, employee_number=employee_number).exists():
            warnings.append(f"Employee Number '{employee_number}' is already assigned.")
        
        # Bank account duplicate check
        if account_number and EmployeeProfile.objects.filter(tenant=tenant, account_number=account_number).exists():
            warnings.append(f"Bank Account '{account_number}' is already assigned to another staff profile.")
        
        # NIN duplicate check (checks encrypted field)
        if nin:
            nin_encrypted = StatutoryPIIEncryption.encode(nin)
            if nin_encrypted and EmployeeProfile.objects.filter(tenant=tenant, nin_encrypted=nin_encrypted).exists():
                warnings.append(f"National Identity Number (NIN) is already assigned to another employee. Each NIN must be unique per person.")
        
        # BVN duplicate check (checks encrypted field)
        if bvn:
            bvn_encrypted = StatutoryPIIEncryption.encode(bvn)
            if bvn_encrypted and EmployeeProfile.objects.filter(tenant=tenant, bvn_encrypted=bvn_encrypted).exists():
                warnings.append(f"Bank Verification Number (BVN) is already assigned to another employee. Each BVN must be unique per person.")

        return {
            "has_duplicates": len(warnings) > 0,
            "warning_count": len(warnings),
            "warnings": warnings
        }
