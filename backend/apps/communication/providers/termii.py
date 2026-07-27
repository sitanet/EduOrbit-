import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

class TermiiSMSProvider:
    """
    Termii SMS Gateway Provider for EduOrbit ERP.
    Endpoint: https://api.ng.termii.com/api/sms/send
    """
    @classmethod
    def send_sms(cls, to_phone, message, sender_id=None, channel="generic"):
        api_key = getattr(settings, 'TERMII_API_KEY', 'test_termii_api_key_123')
        default_sender = getattr(settings, 'TERMII_SENDER_ID', 'EduOrbit')
        base_url = getattr(settings, 'TERMII_BASE_URL', 'https://api.ng.termii.com')
        
        url = f"{base_url.rstrip('/')}/api/sms/send"
        
        # Format destination phone number to international e.164 format (e.g. 2348012345678)
        phone_clean = str(to_phone).replace('+', '').replace(' ', '').replace('-', '')
        if phone_clean.startswith('0'):
            phone_clean = '234' + phone_clean[1:]  # Default Nigeria country code

        payload = {
            "to": phone_clean,
            "from": sender_id or default_sender,
            "sms": message,
            "type": "plain",
            "channel": channel,
            "api_key": api_key
        }

        try:
            # If in test/mock mode or no live HTTP requests
            if api_key.startswith('test_') or getattr(settings, 'MOCK_THIRD_PARTY_APIS', True):
                logger.info(f"[Termii SMS Mock] Sent to {phone_clean} via sender '{payload['from']}': {message[:40]}...")
                return {
                    "status": "success",
                    "provider": "Termii SMS",
                    "message_id": f"termii_msg_{phone_clean[-6:]}",
                    "recipient": phone_clean,
                    "code": "ok"
                }

            headers = {'Content-Type': 'application/json'}
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            data = response.json()
            
            if response.status_code == 200 and data.get("code") == "ok":
                logger.info(f"[Termii SMS] Successfully sent to {phone_clean}")
                return {"status": "success", "provider": "Termii SMS", "response": data}
            else:
                logger.error(f"[Termii SMS Error] {data}")
                return {"status": "error", "provider": "Termii SMS", "response": data}

        except Exception as e:
            logger.error(f"[Termii SMS Exception] Failed sending to {phone_clean}: {str(e)}")
            return {"status": "error", "provider": "Termii SMS", "error": str(e)}
