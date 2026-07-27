import logging
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)

class HostingerEmailProvider:
    """
    Hostinger SMTP Email Dispatcher for EduOrbit ERP.
    Host: smtp.hostinger.com | Port: 465 (SSL) / 587 (TLS)
    """
    @classmethod
    def send_email(cls, recipient_email, subject, message_body, html_body=None, from_email=None):
        sender = from_email or getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@eduorbit.com')
        try:
            sent_count = send_mail(
                subject=subject,
                message=message_body,
                from_email=sender,
                recipient_list=[recipient_email] if isinstance(recipient_email, str) else recipient_email,
                html_message=html_body,
                fail_silently=False,
            )
            logger.info(f"[Hostinger Mail] Successfully dispatched email to {recipient_email}")
            return {"status": "success", "provider": "Hostinger SMTP", "messages_sent": sent_count}
        except Exception as e:
            logger.error(f"[Hostinger Mail Error] Failed to send email to {recipient_email}: {str(e)}")
            return {"status": "error", "provider": "Hostinger SMTP", "error": str(e)}
