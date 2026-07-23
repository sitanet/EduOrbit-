from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger("eduorbit.notifications")

class INotificationChannel(ABC):
    @abstractmethod
    def send(self, recipient_id: str, payload: Dict[str, Any], tenant_id: str) -> bool:
        """Sends notification through concrete delivery channel."""
        pass


class NotificationBus:
    """
    Unified Notification pipeline coordinating delivery across Email, SMS, WhatsApp, Push, and WebSockets.
    """
    def __init__(self):
        self._channels: Dict[str, INotificationChannel] = {}

    def register_channel(self, name: str, channel: INotificationChannel):
        self._channels[name] = channel
        logger.info(f"Notification channel '{name}' registered.")

    def dispatch(self, 
                 recipient_id: str, 
                 channels: List[str], 
                 payload: Dict[str, Any], 
                 tenant_id: str):
        """
        Distributes message to requested channels.
        """
        for channel_name in channels:
            channel = self._channels.get(channel_name)
            if not channel:
                logger.warning(f"Notification channel '{channel_name}' not registered. Skipping.")
                continue
            
            try:
                # Dispatch execution
                channel.send(recipient_id, payload, tenant_id)
            except Exception as e:
                logger.error(f"Failed delivery on channel '{channel_name}' to recipient {recipient_id}: {str(e)}", exc_info=True)


# Global notification manager
notification_bus = NotificationBus()


# ==============================================================
# PLACEHOLDER CHANNELS FOR TESTING THE INTEGRATION
# ==============================================================

class EmailChannel(INotificationChannel):
    def send(self, recipient_id: str, payload: Dict[str, Any], tenant_id: str) -> bool:
        logger.info(f"[Email Channel] Sent to {recipient_id} | Subject: {payload.get('subject')}")
        return True

class SMSChannel(INotificationChannel):
    def send(self, recipient_id: str, payload: Dict[str, Any], tenant_id: str) -> bool:
        logger.info(f"[SMS Channel] Sent to {recipient_id} | Body: {payload.get('body')}")
        return True

# Register channels on load
notification_bus.register_channel("email", EmailChannel())
notification_bus.register_channel("sms", SMSChannel())
