import re
from django.db import transaction
from backend.apps.hr.models import EmployeeProfile

class EmployeeNumberGeneratorService:
    """
    Pattern-based configurable Employee Number Generator per tenant.
    Examples: 'SCH-{YEAR}-{SEQ:5}', 'LAG-STAFF-{SEQ:4}', 'ABJ-HR-2026-{SEQ:5}'
    """

    @classmethod
    def generate(cls, tenant, pattern="SCH-{YEAR}-{SEQ:5}"):
        with transaction.atomic():
            import datetime
            year_str = str(datetime.date.today().year)
            
            # Find current max sequence for pattern
            pattern_prefix = pattern.split('{SEQ:')[0].replace('{YEAR}', year_str)
            existing_count = EmployeeProfile.objects.filter(employee_number__startswith=pattern_prefix).count()
            next_seq = existing_count + 1
            
            # Match {SEQ:n}
            seq_match = re.search(r'\{SEQ:(\d+)\}', pattern)
            seq_padding = int(seq_match.group(1)) if seq_match else 5
            seq_str = str(next_seq).zfill(seq_padding)
            
            employee_num = pattern.replace('{YEAR}', year_str)
            employee_num = re.sub(r'\{SEQ:\d+\}', seq_str, employee_num)
            
            # Guarantee uniqueness
            while EmployeeProfile.objects.filter(employee_number=employee_num).exists():
                next_seq += 1
                seq_str = str(next_seq).zfill(seq_padding)
                employee_num = pattern.replace('{YEAR}', year_str)
                employee_num = re.sub(r'\{SEQ:\d+\}', seq_str, employee_num)

            return employee_num
