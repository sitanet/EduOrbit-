from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from django.contrib.auth import authenticate
from backend.apps.identity.models import User

class IAuthenticationProvider(ABC):
    """
    Interface for dynamic identity verification engines.
    """
    @abstractmethod
    def authenticate_user(self, credentials: Dict[str, Any]) -> Optional[User]:
        """Verify user credentials and return User if verified, else None."""
        pass


class PasswordProvider(IAuthenticationProvider):
    """
    Concrete Password provider validating username/email and password parameters.
    """
    def authenticate_user(self, credentials: Dict[str, Any]) -> Optional[User]:
        login_identifier = credentials.get("username") or credentials.get("email")
        password = credentials.get("password")
        
        if not login_identifier or not password:
            return None
            
        # Django authenticate helper resolves custom backend validations
        user = authenticate(username=login_identifier, password=password)
        if user and user.is_active:
            return user
        return None


class OtpProvider(IAuthenticationProvider):
    """
    Placeholder for OTP verification login.
    """
    def authenticate_user(self, credentials: Dict[str, Any]) -> Optional[User]:
        phone_or_email = credentials.get("username")
        otp_code = credentials.get("otp")
        # Validation checks go here
        return None


class AuthenticationProviderRegistry:
    """
    Orchestration registry resolving identity verification methods.
    """
    def __init__(self):
        self._providers: Dict[str, IAuthenticationProvider] = {}

    def register(self, method: str, provider: IAuthenticationProvider):
        self._providers[method] = provider

    def get_provider(self, method: str) -> IAuthenticationProvider:
        provider = self._providers.get(name := method.lower())
        if not provider:
            raise ValueError(f"Authentication provider method '{name}' is not registered.")
        return provider

# Global registry locator
auth_provider_registry = AuthenticationProviderRegistry()

# Default registrations
auth_provider_registry.register("password", PasswordProvider())
auth_provider_registry.register("otp", OtpProvider())
