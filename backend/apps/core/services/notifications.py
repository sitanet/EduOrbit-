import logging
from django.conf import settings
from django.utils import timezone
from backend.apps.communication.providers.hostinger_mail import HostingerEmailProvider
from backend.apps.communication.providers.termii import TermiiSMSProvider

logger = logging.getLogger(__name__)

class UnifiedNotificationService:
    """
    Enterprise Shared Notification Service.
    Integrates Hostinger SMTP Email and Termii SMS Gateway providers.
    """
    @classmethod
    def send_notification(cls, recipient, title, message, channels=None, metadata=None):
        channels = channels or ['in_app', 'email']
        metadata = metadata or {}
        results = {}

        if 'in_app' in channels:
            results['in_app'] = cls._send_in_app(recipient, title, message, metadata)

        if 'email' in channels:
            recipient_email = metadata.get('email', recipient if '@' in str(recipient) else 'user@eduorbit.com')
            results['email'] = HostingerEmailProvider.send_email(
                recipient_email=recipient_email,
                subject=title,
                message_body=message
            )

        if 'sms' in channels:
            recipient_phone = metadata.get('phone', recipient)
            results['sms'] = TermiiSMSProvider.send_sms(
                to_phone=recipient_phone,
                message=message
            )

        if 'push' in channels:
            results['push'] = cls._send_push(recipient, title, message, metadata)

        return {
            "status": "success",
            "timestamp": timezone.now().isoformat(),
            "channel_results": results
        }

    @classmethod
    def _send_in_app(cls, recipient, title, message, metadata):
        logger.info(f"[In-App Notification] To: {recipient} | Title: {title}")
        return {"channel": "in_app", "status": "delivered"}

    @classmethod
    def _send_push(cls, recipient, title, message, metadata):
        logger.info(f"[Push Notification] To: {recipient} | Title: {title}")
        return {"channel": "push", "status": "sent"}
