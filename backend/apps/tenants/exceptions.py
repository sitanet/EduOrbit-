"""
EduOrbit Platform Custom Domain Exceptions.
Provides strongly-typed domain exception classes for business rule and subscription errors.
"""

class EduOrbitSubscriptionException(Exception):
    """Base domain exception for EduOrbit subscription and billing system."""
    pass

class SubscriptionException(EduOrbitSubscriptionException):
    """Raised for general subscription lifecycle errors."""
    pass

class InvoiceException(EduOrbitSubscriptionException):
    """Raised for invoice state or processing errors."""
    pass

class BillingException(EduOrbitSubscriptionException):
    """Raised for billing calculation or tier pricing errors."""
    pass

class ComplianceException(EduOrbitSubscriptionException):
    """Raised for school compliance threshold errors."""
    pass

class PaymentPolicyException(EduOrbitSubscriptionException):
    """Raised when a payment policy validation fails."""
    pass

class ValidationException(EduOrbitSubscriptionException):
    """Raised for data validation or precondition failures."""
    pass
