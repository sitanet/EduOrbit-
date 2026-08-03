"""
Abstract Payment Gateway Interface & Gateway Factory for EduOrbit SaaS Platform.
Provides a pluggable, gateway-agnostic contract for all payment provider integrations (Paystack, OPay, etc.).
"""

import logging
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Dict, Any, Optional

from backend.apps.tenants.dto import ServiceResult

logger = logging.getLogger(__name__)


class PaymentGateway(ABC):
    """
    Abstract Base Class for all EduOrbit Payment Provider Implementations.
    Guarantees pluggable multi-gateway support without altering business domain logic.
    """

    @abstractmethod
    def get_provider_name(self) -> str:
        """Returns uppercase provider code (e.g., 'PAYSTACK', 'OPAY')."""
        pass

    @abstractmethod
    def initialize_transaction(
        self,
        amount: Decimal,
        reference: str,
        customer_email: str,
        callback_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ServiceResult:
        """
        Initializes payment transaction with gateway provider API and returns checkout URL.
        """
        pass

    @abstractmethod
    def verify_transaction(self, reference: str) -> ServiceResult:
        """
        Verifies transaction status directly with gateway API using reference.
        """
        pass

    @abstractmethod
    def verify_webhook_signature(self, payload: Dict[str, Any], signature_header: str) -> bool:
        """
        Validates HMAC signature of incoming gateway webhook request payload.
        """
        pass

    @abstractmethod
    def normalize_response(self, raw_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalizes gateway webhook payload into standardized dict format:
        {'reference': str, 'amount': Decimal, 'event_type': str, 'is_success': bool}
        """
        pass


class PaymentGatewayFactory:
    """
    Factory resolving concrete PaymentGateway implementations dynamically at runtime.
    """

    @classmethod
    def get_gateway(cls, provider_name: str = "PAYSTACK") -> PaymentGateway:
        """
        Returns concrete PaymentGateway instance for provider_name.
        """
        provider = str(provider_name).strip().upper()

        if provider == "PAYSTACK":
            from backend.apps.tenants.services.paystack_gateway import PaystackGateway
            return PaystackGateway()
        elif provider == "OPAY":
            from backend.apps.tenants.services.opay_gateway import OPayGateway
            return OPayGateway()

        raise ValueError(f"Unsupported payment gateway provider: '{provider_name}'")
