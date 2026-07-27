class OnboardingReadinessService:
    """
    Evaluates 14-Point Onboarding & Payroll Readiness Checklist.
    """
    @classmethod
    def evaluate_readiness(cls, employee_profile):
        checklist = [
            ("Personal Demographics", bool(employee_profile.person.first_name and employee_profile.person.last_name)),
            ("NIN Verification", employee_profile.is_nin_verified),
            ("BVN Verification", employee_profile.is_bvn_verified),
            ("Employee Number", bool(employee_profile.employee_number)),
            ("Job Designation", bool(employee_profile.job_title)),
            ("Department Assignment", bool(employee_profile.department_name)),
            ("Campus Assignment", bool(employee_profile.campus_name)),
            ("Cost Centre Tagging", bool(employee_profile.cost_centre)),
            ("Bank Account Details", bool(employee_profile.account_number and employee_profile.bank_name)),
            ("PFA & RSA PIN", bool(employee_profile.pfa_name or employee_profile.rsa_pin_encrypted)),
            ("Tax ID Setup", bool(employee_profile.tax_id_encrypted)),
            ("Salary Compensation Grade", bool(employee_profile.salary_grade)),
            ("Emergency Contacts", bool(employee_profile.next_of_kin_name and employee_profile.next_of_kin_phone)),
            ("User Account Setup", bool(employee_profile.person.user_id)),
        ]
        
        passed_count = sum(1 for _, is_passed in checklist if is_passed)
        total_count = len(checklist)
        percentage = round((passed_count / total_count) * 100, 1)

        return {
            "readiness_percentage": percentage,
            "is_payroll_ready": percentage >= 80.0,
            "checklist_items": [{"criterion": item, "is_passed": status} for item, status in checklist]
        }
