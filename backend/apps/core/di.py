from abc import ABC, abstractmethod
from typing import Dict, Any, Type, Dict

# ==============================================================
# INTERFACES
# ==============================================================

class IStorageProvider(ABC):
    @abstractmethod
    def save_file(self, path: str, content) -> str:
        pass

    @abstractmethod
    def delete_file(self, path: str) -> bool:
        pass

    @abstractmethod
    def get_url(self, path: str) -> str:
        pass


class IPaymentGateway(ABC):
    @abstractmethod
    def create_customer(self, tenant_name: str, email: str) -> str:
        pass

    @abstractmethod
    def create_subscription(self, customer_id: str, plan_price_id: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def process_webhook(self, payload: Dict[str, Any], headers: Dict[str, Any]) -> bool:
        pass


class IAIProvider(ABC):
    @abstractmethod
    def generate_text(self, prompt: str, system_instruction: str = None, temperature: float = 0.2) -> str:
        pass


# ==============================================================
# DEPENDENCY INJECTION DI CONTAINER
# ==============================================================

class DependencyContainer:
    """
    Enterprise IoC Container supporting interface-to-implementation binding maps.
    Enforces abstract boundary interfaces and dynamic component resolution.
    """
    def __init__(self):
        self._registry: Dict[Type, Type] = {}
        self._instances: Dict[Type, Any] = {}

    def register(self, interface: Type, implementation: Type):
        """
        Binds an interface to a concrete class type.
        """
        if not issubclass(implementation, interface) and implementation != interface:
            raise TypeError(f"Implementation {implementation.__name__} does not subclass {interface.__name__}")
        self._registry[interface] = implementation
        # Clear out any pre-cached singletons if we re-register
        if interface in self._instances:
            del self._instances[interface]

    def resolve(self, interface: Type) -> Any:
        """
        Resolves the concrete implementation registered for the interface.
        Caches and returns as a singleton.
        """
        if interface in self._instances:
            return self._instances[interface]
            
        implementation = self._registry.get(interface)
        if not implementation:
            raise ValueError(f"No implementation registered for interface: {interface.__name__}")
            
        instance = implementation()
        self._instances[interface] = instance
        return instance

# Global container instance
ioc = DependencyContainer()
