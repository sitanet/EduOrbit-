from abc import ABC, abstractmethod

class SMSGatewayAdapter(ABC):
    """
    Interface for third-party SMS messaging providers (e.g. Twilio, Infobip, Africa's Talking).
    """
    @abstractmethod
    def send_sms(self, phone_number: str, message: str, sender_id: str = None) -> bool:
        """Deliver outgoing SMS message to destination phone number."""
        pass
