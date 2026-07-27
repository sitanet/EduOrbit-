from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List
from decimal import Decimal

@dataclass(frozen=True)
class PayrollPostingLine:
    account_name: str
    amount: Decimal
    entry_type: str  # 'debit' or 'credit'

@dataclass(frozen=True)
class PayrollPostingCommand:
    idempotency_key: str  # tenant_uuid:payroll_run_uuid:posting_version:ledger_version
    event_type: str
    tenant_id: str
    lines: List[PayrollPostingLine]

class AccountingPostingInterface(ABC):
    @abstractmethod
    def post_payroll(self, command: PayrollPostingCommand) -> None:
        pass
