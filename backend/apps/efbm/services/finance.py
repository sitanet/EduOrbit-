from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from backend.apps.core.interfaces import AccountingPostingInterface, PayrollPostingCommand
from backend.apps.efbm.models import JournalEvent, JournalEntry, LedgerPosting

class AccountingService(AccountingPostingInterface):
    @transaction.atomic
    def post_payroll(self, command: PayrollPostingCommand) -> None:
        tenant_id = command.tenant_id
        
        # Enforce idempotency by embedding key in CharField event_type
        event_str = f"payroll_post:{command.idempotency_key}"
        if len(event_str) > 100:
            event_str = event_str[:100]  # Safe truncation within CharField limit
            
        event, created = JournalEvent.objects.get_or_create(
            tenant_id=tenant_id,
            event_type=event_str,
            defaults={"timestamp": timezone.now()}
        )
        
        if not created:
            # Idempotency safety: transaction already posted and committed previously
            return

        # Double-entry validation: sum of debits must equal sum of credits
        debit_sum = 0
        credit_sum = 0
        for line in command.lines:
            if line.entry_type == 'debit':
                debit_sum += line.amount
            elif line.entry_type == 'credit':
                credit_sum += line.amount
                
        if debit_sum != credit_sum:
            raise ValidationError(f"Double-entry validation failed: debits ({debit_sum}) must equal credits ({credit_sum}).")

        # Save journal entries & ledger postings
        for line in command.lines:
            entry = JournalEntry.objects.create(
                tenant_id=tenant_id,
                event=event,
                account_name=line.account_name,
                amount=line.amount,
                entry_type=line.entry_type
            )
            LedgerPosting.objects.create(
                tenant_id=tenant_id,
                entry=entry,
                posting_date=timezone.now().date()
            )
