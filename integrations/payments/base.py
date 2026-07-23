from abc import ABC, abstractmethod
from typing import Dict, Any

class PaymentGatewayAdapter(ABC):
    """
    Interface for third-party billing/subscription processors.
    """
    @abstractmethod
    def create_customer(self, tenant_name: str, email: str) -> str:
        """Create a client account profile and return provider customer reference ID."""
        pass

    @abstractmethod
    def create_subscription(self, customer_id: str, plan_price_id: str) -> Dict[str, Any]:
        """Initiate payment subscription recurring billing plan."""
        pass

    @abstractmethod
    def process_webhook(self, payload: Dict[str, Any], headers: Dict[str, Any]) -> bool:
        """Parse subscription cycle charge successes, failures, or updates."""
        pass
