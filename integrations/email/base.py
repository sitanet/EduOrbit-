from abc import ABC, abstractmethod
from typing import List, Dict, Any

class EmailGatewayAdapter(ABC):
    """
    Interface for third-party email providers (e.g. Mailgun, SendGrid, Amazon SES).
    """
    @abstractmethod
    def send_email(self, 
                   to_emails: List[str], 
                   subject: str, 
                   html_content: str, 
                   text_content: str = "", 
                   from_email: str = None,
                   attachments: List[Dict[str, Any]] = None) -> bool:
        """Deliver outgoing HTML email."""
        pass
