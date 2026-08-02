import os
import requests
from abc import ABC, abstractmethod
from django.conf import settings
from django.utils import timezone


class AbstractKYCProvider(ABC):
    @abstractmethod
    def verify_nin(self, nin_number):
        pass

    @abstractmethod
    def verify_bvn(self, bvn_number):
        pass

    @abstractmethod
    def resolve_bank_account(self, bank_code, account_number):
        pass


class DojahKYCProvider(AbstractKYCProvider):
    def __init__(self, api_key=None, app_id=None):
        self.api_key = api_key or getattr(settings, 'DOJAH_API_KEY', os.getenv('DOJAH_API_KEY'))
        self.app_id = app_id or getattr(settings, 'DOJAH_APP_ID', os.getenv('DOJAH_APP_ID'))
        self.base_url = getattr(settings, 'DOJAH_BASE_URL', 'https://api.dojah.io')

    def verify_nin(self, nin_number):
        if not self.api_key or not self.app_id:
            return SandboxKYCProvider().verify_nin(nin_number)
        
        headers = {
            "Authorization": self.api_key,
            "AppId": self.app_id,
            "Accept": "application/json"
        }
        try:
            resp = requests.get(f"{self.base_url}/api/v1/kyc/nin?nin={nin_number}", headers=headers, timeout=10)
            res_json = resp.json()
            if resp.status_code == 200 and 'entity' in res_json:
                data = res_json.get('entity', {})
                fn = data.get('first_name') or data.get('firstname') or ''
                mn = data.get('middle_name') or data.get('middlename') or ''
                ln = data.get('last_name') or data.get('lastname') or data.get('surname') or ''
                full_name = f"{fn} {mn} {ln}".strip() or data.get('full_name') or data.get('name') or "NIN Holder"
                dob = data.get('date_of_birth') or data.get('dob') or data.get('birthdate') or "N/A"
                gender = data.get('gender') or data.get('sex') or "N/A"
                photo = data.get('photo') or data.get('image') or ""

                return {
                    "status": "success",
                    "is_verified": True,
                    "provider": "Dojah Live API",
                    "data": {
                        "full_name": full_name,
                        "first_name": fn,
                        "middle_name": mn,
                        "last_name": ln,
                        "dob": dob,
                        "gender": gender,
                        "photo_url": photo,
                        "timestamp": timezone.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                }
            elif resp.status_code == 401:
                return {
                    "status": "error",
                    "is_verified": False,
                    "provider": "Dojah Live API",
                    "message": "Dojah Authorization Failed (401). Please set DOJAH_API_KEY in backend/.env to your Production Secret Key (prod_sk_...)"
                }
            elif resp.status_code == 402:
                return {
                    "status": "error",
                    "is_verified": False,
                    "provider": "Dojah Live API",
                    "message": "Dojah Wallet Balance Low (402): Your balance is low, please top up your Dojah wallet on the Dojah dashboard."
                }
            else:
                err_msg = res_json.get('error') or res_json.get('message') or f"Dojah API returned HTTP {resp.status_code}"
                return {"status": "error", "is_verified": False, "provider": "Dojah Live API", "message": err_msg}
        except requests.exceptions.ConnectionError:
            return {
                "status": "error",
                "is_verified": False,
                "provider": "Dojah Live API",
                "message": "Unable to connect to Dojah verification server. Please check your internet connection and try again."
            }
        except requests.exceptions.Timeout:
            return {
                "status": "error",
                "is_verified": False,
                "provider": "Dojah Live API",
                "message": "Verification request timed out. Please try again."
            }
        except Exception as e:
            return {
                "status": "error",
                "is_verified": False,
                "provider": "Dojah Live API",
                "message": "Verification failed due to a network error. Please try again."
            }

    def verify_bvn(self, bvn_number):
        if not self.api_key or not self.app_id:
            return SandboxKYCProvider().verify_bvn(bvn_number)
        
        headers = {
            "Authorization": self.api_key,
            "AppId": self.app_id,
            "Accept": "application/json"
        }
        try:
            resp = requests.get(f"{self.base_url}/api/v1/kyc/bvn/full?bvn={bvn_number}", headers=headers, timeout=10)
            res_json = resp.json()
            if resp.status_code != 200 or 'entity' not in res_json:
                resp = requests.get(f"{self.base_url}/api/v1/kyc/bvn?bvn={bvn_number}", headers=headers, timeout=10)
                res_json = resp.json()

            if resp.status_code == 200 and 'entity' in res_json:
                data = res_json.get('entity', {})
                fn = data.get('first_name') or data.get('firstname') or ''
                mn = data.get('middle_name') or data.get('middlename') or ''
                ln = data.get('last_name') or data.get('lastname') or data.get('surname') or ''
                full_name = f"{fn} {mn} {ln}".strip() or data.get('full_name') or data.get('name') or "BVN Holder"
                dob = data.get('date_of_birth') or data.get('dob') or data.get('birthdate') or "N/A"
                gender = data.get('gender') or data.get('sex') or "N/A"

                return {
                    "status": "success",
                    "is_verified": True,
                    "provider": "Dojah Live API",
                    "data": {
                        "full_name": full_name,
                        "first_name": fn,
                        "middle_name": mn,
                        "last_name": ln,
                        "dob": dob,
                        "gender": gender,
                        "timestamp": timezone.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                }
            elif resp.status_code == 401:
                return {
                    "status": "error",
                    "is_verified": False,
                    "provider": "Dojah Live API",
                    "message": "Dojah Authorization Failed (401). Please set DOJAH_API_KEY in backend/.env to your Production Secret Key (prod_sk_...)"
                }
            elif resp.status_code == 402:
                return {
                    "status": "error",
                    "is_verified": False,
                    "provider": "Dojah Live API",
                    "message": "Dojah Wallet Balance Low (402): Your balance is low, please top up your Dojah wallet on the Dojah dashboard."
                }
            else:
                err_msg = res_json.get('error') or res_json.get('message') or f"Dojah API returned HTTP {resp.status_code}"
                return {"status": "error", "is_verified": False, "provider": "Dojah Live API", "message": err_msg}
        except requests.exceptions.ConnectionError:
            return {
                "status": "error",
                "is_verified": False,
                "provider": "Dojah Live API",
                "message": "Unable to connect to Dojah verification server. Please check your internet connection and try again."
            }
        except requests.exceptions.Timeout:
            return {
                "status": "error",
                "is_verified": False,
                "provider": "Dojah Live API",
                "message": "Verification request timed out. Please try again."
            }
        except Exception as e:
            return {
                "status": "error",
                "is_verified": False,
                "provider": "Dojah Live API",
                "message": "Verification failed due to a network error. Please try again."
            }

    def resolve_bank_account(self, bank_code, account_number):
        if not self.api_key or not self.app_id:
            return SandboxKYCProvider().resolve_bank_account(bank_code, account_number)
        
        headers = {
            "Authorization": self.api_key,
            "AppId": self.app_id,
            "Accept": "application/json"
        }
        try:
            resp = requests.get(f"{self.base_url}/api/v1/general/account?account_number={account_number}&bank_code={bank_code}", headers=headers, timeout=10)
            res_json = resp.json()
            if resp.status_code == 200 and 'entity' in res_json:
                data = res_json.get('entity', {})
                return {
                    "status": "success",
                    "is_resolved": True,
                    "provider": "Dojah Live NUBAN API",
                    "data": {
                        "account_name": data.get('account_name', 'N/A'),
                        "account_number": data.get('account_number', account_number),
                        "bank_code": bank_code,
                        "bank_name": data.get('bank_name', '')
                    }
                }
            elif resp.status_code == 401:
                return {
                    "status": "error",
                    "is_resolved": False,
                    "message": "Dojah Authorization Failed (401). Please set DOJAH_API_KEY in backend/.env to your Production Secret Key (prod_sk_...)"
                }
            else:
                err_msg = res_json.get('error') or res_json.get('message') or f"Dojah API returned HTTP {resp.status_code}"
                return {"status": "error", "is_resolved": False, "message": err_msg}
        except requests.exceptions.ConnectionError:
            return {"status": "error", "is_resolved": False, "message": "Unable to connect to Dojah verification server. Please check your internet connection and try again."}
        except requests.exceptions.Timeout:
            return {"status": "error", "is_resolved": False, "message": "Verification request timed out. Please try again."}
        except Exception as e:
            return {"status": "error", "is_resolved": False, "message": "Bank resolution failed due to a network error. Please try again."}


class SandboxKYCProvider(AbstractKYCProvider):
    """
    Zero-config Sandbox Simulator Mode.
    Automatically used when Dojah API keys are not configured.
    """
    def verify_nin(self, nin_number):
        if len(str(nin_number)) == 11:
            return {
                "status": "success",
                "is_verified": True,
                "provider": "Dojah Sandbox",
                "data": {
                    "full_name": "Natasha Romanoff",
                    "dob": "1992-06-15",
                    "gender": "Female",
                    "photo_url": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150",
                    "nin": str(nin_number),
                    "timestamp": timezone.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            }
        return {"status": "error", "is_verified": False, "provider": "Dojah Sandbox", "message": "Invalid 11-digit NIN"}

    def verify_bvn(self, bvn_number):
        if len(str(bvn_number)) == 11:
            return {
                "status": "success",
                "is_verified": True,
                "provider": "Dojah Sandbox",
                "data": {
                    "full_name": "Natasha Romanoff",
                    "bvn": str(bvn_number),
                    "timestamp": timezone.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            }
        return {"status": "error", "is_verified": False, "provider": "Dojah Sandbox", "message": "Invalid 11-digit BVN"}

    def resolve_bank_account(self, bank_code, account_number):
        if len(str(account_number)) == 10:
            return {
                "status": "success",
                "is_resolved": True,
                "provider": "Interswitch NUBAN Sandbox",
                "data": {
                    "account_name": "NATASHA ROMANOFF",
                    "account_number": str(account_number),
                    "bank_code": bank_code or "058",
                    "bank_name": "GTBank PLC"
                }
            }
        return {"status": "error", "is_resolved": False, "message": "Invalid 10-digit NUBAN account number"}


def get_kyc_provider():
    api_key = getattr(settings, 'DOJAH_API_KEY', os.getenv('DOJAH_API_KEY'))
    if api_key:
        return DojahKYCProvider(api_key=api_key)
    return SandboxKYCProvider()
