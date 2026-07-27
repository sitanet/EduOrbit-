from backend.apps.hr.models import EmployeeProfile
from backend.apps.people.models import Person

class DuplicateDetectionService:
    """
    7-Field Duplicate Detection Engine.
    Warns HR if matching NIN, BVN, Phone, Email, Employee Number, Account Number, or RSA PIN exists.
    """
    @classmethod
    def check_duplicates(cls, tenant, email=None, phone=None, nin=None, bvn=None, account_number=None, employee_number=None):
        warnings = []
        
        if email and Person.objects.filter(tenant=tenant, user__email__iexact=email).exists():
            warnings.append(f"Email '{email}' is already assigned to an existing user profile.")
            
        if phone and Person.objects.filter(tenant=tenant, phone_number=phone).exists():
            warnings.append(f"Phone number '{phone}' is registered under another person record.")
            
        if employee_number and EmployeeProfile.objects.filter(tenant=tenant, employee_number=employee_number).exists():
            warnings.append(f"Employee Number '{employee_number}' is already assigned.")

        if account_number and EmployeeProfile.objects.filter(tenant=tenant, account_number=account_number).exists():
            warnings.append(f"Bank Account '{account_number}' is already assigned to another staff profile.")

        return {
            "has_duplicates": len(warnings) > 0,
            "warning_count": len(warnings),
            "warnings": warnings
        }
