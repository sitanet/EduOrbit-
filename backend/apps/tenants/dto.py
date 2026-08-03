"""
EduOrbit Data Transfer Objects (DTO) and Standardized Service Response Container.
"""

from dataclasses import dataclass, field
from typing import Any, List, Dict, Optional

@dataclass
class ServiceResult:
    """
    Strongly-typed, standardized result wrapper returned by all EduOrbit services.
    Guarantees consistent response structure for Web, REST APIs, and Flutter mobile apps.
    """
    success: bool
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts ServiceResult instance to a standard JSON-serializable dictionary.
        """
        return {
            "success": self.success,
            "message": self.message,
            "data": self.data,
            "errors": self.errors
        }

    @classmethod
    def ok(cls, data: Optional[Dict[str, Any]] = None, message: str = "Operation successful") -> 'ServiceResult':
        """
        Factory helper for successful service responses.
        """
        return cls(
            success=True,
            message=message,
            data=data or {},
            errors=[]
        )

    @classmethod
    def fail(cls, message: str, errors: Optional[List[str]] = None, data: Optional[Dict[str, Any]] = None) -> 'ServiceResult':
        """
        Factory helper for failed service responses.
        """
        err_list = errors if errors is not None else [message]
        return cls(
            success=False,
            message=message,
            data=data or {},
            errors=err_list
        )
