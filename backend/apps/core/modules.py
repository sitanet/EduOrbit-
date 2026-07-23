from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class ModuleMetadata:
    """
    Metadata representation of an optional system application module.
    """
    name: str
    version: str
    description: str = ""
    dependencies: List[str] = field(default_factory=list)
    required_permissions: List[str] = field(default_factory=list)
    routes_prefix: str = ""
    navigation_label: str = ""
    navigation_icon: str = ""
    feature_flags: List[str] = field(default_factory=list)
    billing_plans_required: List[str] = field(default_factory=list)

class ModuleRegistry:
    """
    Registry framework manager of all optional/marketplace applications.
    Allows enabling and disabling modules dynamically at runtime.
    """
    def __init__(self):
        self._modules: Dict[str, ModuleMetadata] = {}
        self._active_status: Dict[str, bool] = {}

    def register(self, metadata: ModuleMetadata, default_enabled: bool = False):
        """
        Register a module configuration profile.
        """
        self._modules[metadata.name] = metadata
        self._active_status[metadata.name] = default_enabled

    def enable(self, name: str):
        if name not in self._modules:
            raise KeyError(f"Module {name} is not registered in registry.")
        self._active_status[name] = True

    def disable(self, name: str):
        if name not in self._modules:
            raise KeyError(f"Module {name} is not registered in registry.")
        self._active_status[name] = False

    def is_enabled(self, name: str) -> bool:
        """
        Checks if module is active.
        """
        return self._active_status.get(name, False)

    def get_metadata(self, name: str) -> Optional[ModuleMetadata]:
        return self._modules.get(name)

    def list_all(self) -> Dict[str, ModuleMetadata]:
        return self._modules

    def list_active(self) -> List[str]:
        return [name for name, active in self._active_status.items() if active]

# Global modules registry
module_registry = ModuleRegistry()

# Initialize registry with some standard marketplace optional module descriptors
module_registry.register(ModuleMetadata(
    name="admissions",
    version="1.0.0",
    description="Online application registration & processing module",
    navigation_label="Admissions",
    navigation_icon="school",
    feature_flags=["admissions_active"]
), default_enabled=True)

module_registry.register(ModuleMetadata(
    name="hostel",
    version="1.0.0",
    description="Room and accommodation allocator details",
    navigation_label="Hostels Management",
    navigation_icon="hotel",
    feature_flags=["hostel_active"]
), default_enabled=False)

module_registry.register(ModuleMetadata(
    name="ai_tutor",
    version="1.1.0",
    description="AI powered student assistant and homework coach",
    navigation_label="AI Homework Assistant",
    navigation_icon="smart_toy",
    feature_flags=["ai_active"]
), default_enabled=False)
