"""
Phase 12.4.3C — KYC & Dojah Provider Verification
Tests all provider responses including error scenarios
"""
import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings.local')
sys.path.insert(0, r'c:\Users\user\Desktop\Development\SMS')
import django; django.setup()

from unittest.mock import patch, MagicMock
from backend.apps.hr.services.kyc import DojahKYCProvider, SandboxKYCProvider
import requests

PASS = "✓ PASS"
FAIL = "✗ FAIL"

print("=" * 70)
print("PHASE 12.4.3C — KYC PROVIDER VERIFICATION")
print("=" * 70)

# ================================================================
# 1. SANDBOX PROVIDER TESTS
# ================================================================
print("\n[1] Sandbox KYC Provider")
sandbox = SandboxKYCProvider()

# NIN
nin_result = sandbox.verify_nin("12345678901")
ok = nin_result.get('status') == 'success' and nin_result.get('is_verified') == True
print(f"   {PASS if ok else FAIL} sandbox.verify_nin() => status={nin_result.get('status')}, is_verified={nin_result.get('is_verified')}")
if ok:
    data = nin_result.get('data', {})
    print(f"      full_name: {data.get('full_name')}, dob: {data.get('dob')}")

# BVN
bvn_result = sandbox.verify_bvn("22222222222")
ok = bvn_result.get('status') == 'success' and bvn_result.get('is_verified') == True
print(f"   {PASS if ok else FAIL} sandbox.verify_bvn() => status={bvn_result.get('status')}, is_verified={bvn_result.get('is_verified')}")

# Bank resolution
bank_result = sandbox.resolve_bank_account("011", "3012345678")
ok = bank_result.get('status') == 'success'
print(f"   {PASS if ok else FAIL} sandbox.resolve_bank_account() => status={bank_result.get('status')}")

# ================================================================
# 2. DOJAH PRODUCTION PROVIDER ERROR SCENARIOS (mocked)
# ================================================================
print("\n[2] Dojah Production Provider — Error Handling")

provider = DojahKYCProvider(api_key='prod_sk_test', app_id='test_app')

# Connection Error (DNS failure)
with patch('requests.get', side_effect=requests.exceptions.ConnectionError("getaddrinfo failed")):
    result = provider.verify_nin("12345678901")
    ok = result.get('status') == 'error'
    msg = result.get('message', '')
    no_traceback = 'getaddrinfo' not in msg and 'HTTPSConnection' not in msg and 'NameResolution' not in msg
    print(f"   {PASS if ok and no_traceback else FAIL} ConnectionError => user-friendly message: '{msg[:80]}'")
    if not no_traceback:
        print(f"   {FAIL} WARNING: Raw traceback exposed in message!")

# Timeout
with patch('requests.get', side_effect=requests.exceptions.Timeout("timed out")):
    result = provider.verify_nin("12345678901")
    ok = result.get('status') == 'error'
    msg = result.get('message', '')
    print(f"   {PASS if ok else FAIL} Timeout => '{msg[:80]}'")

# 401 Unauthorized
mock_resp = MagicMock()
mock_resp.status_code = 401
mock_resp.json.return_value = {"error": "Unauthorized"}
with patch('requests.get', return_value=mock_resp):
    result = provider.verify_nin("12345678901")
    ok = result.get('status') == 'error'
    msg = result.get('message', '')
    no_traceback = 'Traceback' not in msg
    print(f"   {PASS if ok and no_traceback else FAIL} HTTP 401 => '{msg[:80]}'")

# 402 Wallet Low
mock_resp = MagicMock()
mock_resp.status_code = 402
mock_resp.json.return_value = {"error": "Insufficient balance"}
with patch('requests.get', return_value=mock_resp):
    result = provider.verify_nin("12345678901")
    ok = result.get('status') == 'error'
    msg = result.get('message', '')
    print(f"   {PASS if ok else FAIL} HTTP 402 => '{msg[:80]}'")

# 200 Success (mocked Dojah response)
mock_resp = MagicMock()
mock_resp.status_code = 200
mock_resp.json.return_value = {
    "entity": {
        "firstname": "AMARA",
        "middlename": "CHIDI",
        "surname": "OKONKWO",
        "birthdate": "1990-01-15",
        "gender": "m",
        "photo": "base64encodedphoto..."
    }
}
with patch('requests.get', return_value=mock_resp):
    result = provider.verify_nin("12345678901")
    ok = result.get('status') == 'success' and result.get('is_verified') == True
    data = result.get('data', {})
    print(f"   {PASS if ok else FAIL} HTTP 200 Success => is_verified={result.get('is_verified')}, full_name={data.get('full_name')}")

# BVN same tests
with patch('requests.get', side_effect=requests.exceptions.ConnectionError("getaddrinfo failed")):
    result = provider.verify_bvn("22222222222")
    ok = result.get('status') == 'error'
    msg = result.get('message', '')
    no_traceback = 'getaddrinfo' not in msg
    print(f"   {PASS if ok and no_traceback else FAIL} BVN ConnectionError => user-friendly: '{msg[:80]}'")

# Bank resolution connection error
with patch('requests.get', side_effect=requests.exceptions.ConnectionError("failed")):
    result = provider.resolve_bank_account("011", "3012345678")
    ok = result.get('status') == 'error'
    msg = result.get('message', '')
    no_traceback = 'Traceback' not in msg
    print(f"   {PASS if ok and no_traceback else FAIL} Bank ConnectionError => user-friendly: '{msg[:80]}'")

# ================================================================
# 3. VERIFY NO PYTHON TRACEBACKS EVER EXPOSED
# ================================================================
print("\n[3] Traceback Exposure Audit")
dangerous_patterns = ['Traceback (most recent call last)', 'File "', 'line ', 'HTTPSConnectionPool', 'NameResolutionError', 'getaddrinfo']

all_clean = True
for exc_type, exc in [
    ("ConnectionError", requests.exceptions.ConnectionError("test")),
    ("Timeout", requests.exceptions.Timeout("test")),
]:
    for method in ['verify_nin', 'verify_bvn']:
        with patch('requests.get', side_effect=exc):
            result = getattr(provider, method)("12345678901")
            msg = result.get('message', '')
            for pattern in dangerous_patterns:
                if pattern in msg:
                    all_clean = False
                    print(f"   {FAIL} TRACEBACK EXPOSED in {method}({exc_type}): '{pattern}' found in message")

if all_clean:
    print(f"   {PASS} No Python tracebacks exposed in any error message")

print("\n" + "=" * 70)
print("KYC PROVIDER VERIFICATION COMPLETE")
print("=" * 70)
