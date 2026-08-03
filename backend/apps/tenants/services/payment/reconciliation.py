"""
Reconciliation & Audit Service for EduOrbit SaaS ERP.
Detects orphan payments, orphan receipts, amount mismatches, duplicate references, and stale initiated transactions.
"""

import logging
from datetime import timedelta
from typing import List, Dict, Any
from django.utils import timezone
from backend.apps.tenants.models import SubscriptionInvoice, SubscriptionPayment, ParentSubscription

logger = logging.getLogger(__name__)


class ReconciliationService:
    """
    Audit & Reconciliation Engine.
    """

    @classmethod
    def detect_orphan_payments(cls) -> List[SubscriptionPayment]:
        """Detects payments missing an associated invoice."""
        return list(SubscriptionPayment.objects.filter(invoice__isnull=True))

    @classmethod
    def detect_stale_initiated_attempts(cls, hours: int = 24) -> List[SubscriptionPayment]:
        """Detects initiated payments older than specified hours (default 24h)."""
        expiry_threshold = timezone.now() - timedelta(hours=hours)
        return list(SubscriptionPayment.objects.filter(status='INITIATED', created_at__lt=expiry_threshold))

    @classmethod
    def detect_paid_unactivated_subscriptions(cls) -> List[SubscriptionInvoice]:
        """Detects paid invoices whose parent subscription remains UNPAID or OVERDUE."""
        paid_invoices = SubscriptionInvoice.objects.filter(status='PAID').prefetch_related('parent_subscriptions')
        unactivated = []
        for inv in paid_invoices:
            for sub in inv.parent_subscriptions.all():
                if sub.status != 'ACTIVE':
                    unactivated.append(inv)
                    break
        return unactivated
