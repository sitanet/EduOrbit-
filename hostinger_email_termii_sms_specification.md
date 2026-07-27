# EduOrbit ERP — Hostinger Email & Termii SMS Provider Integration Specification

> **Integration Status**: `ACTIVE & VERIFIED`  
> **Release Tag**: `v3.0.0-COMMUNICATION-PROVIDERS`  
> **Target Date**: July 27, 2026  
> **Scope**: Hostinger SMTP Email Provider and Termii SMS Gateway Integration.

---

## 1. Executive Summary

EduOrbit ERP has been updated with native integration for:
1. **Hostinger SMTP Email Gateway** (`smtp.hostinger.com:465` SSL / `587` TLS).
2. **Termii SMS Gateway** (`https://api.ng.termii.com/api/sms/send`).

---

## 2. Configuration Settings (`backend/config/settings/base.py`)

### A. Hostinger Email Configuration
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env.str('EMAIL_HOST', default='smtp.hostinger.com')
EMAIL_PORT = env.int('EMAIL_PORT', default=465)
EMAIL_USE_SSL = env.bool('EMAIL_USE_SSL', default=True)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=False)
EMAIL_HOST_USER = env.str('EMAIL_HOST_USER', default='noreply@yourdomain.com')
EMAIL_HOST_PASSWORD = env.str('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env.str('DEFAULT_FROM_EMAIL', default='EduOrbit ERP <noreply@yourdomain.com>')
```

### B. Termii SMS Configuration
```python
TERMII_API_KEY = env.str('TERMII_API_KEY', default='your_termii_api_key_here')
TERMII_SENDER_ID = env.str('TERMII_SENDER_ID', default='EduOrbit')
TERMII_BASE_URL = env.str('TERMII_BASE_URL', default='https://api.ng.termii.com')
```

---

## 3. Environment Variables Setup (`.env`)

Add the following to your `.env` file on production:

```env
# Hostinger SMTP Credentials
EMAIL_HOST=smtp.hostinger.com
EMAIL_PORT=465
EMAIL_USE_SSL=True
EMAIL_HOST_USER=noreply@your-school-domain.com
EMAIL_HOST_PASSWORD=your_hostinger_email_password
DEFAULT_FROM_EMAIL=EduOrbit ERP <noreply@your-school-domain.com>

# Termii SMS Gateway Credentials
TERMII_API_KEY=TER_live_xxxxxxxxxxxxxxxxxxxxxxxxxx
TERMII_SENDER_ID=EduOrbit
TERMII_BASE_URL=https://api.ng.termii.com
```

---

## 4. Provider Code Implementations

1. **Hostinger Email Provider**: [hostinger_mail.py](file:///c:/Users/user/Desktop/Development/SMS/backend/apps/communication/providers/hostinger_mail.py)
2. **Termii SMS Provider**: [termii.py](file:///c:/Users/user/Desktop/Development/SMS/backend/apps/communication/providers/termii.py)
3. **Unified Notification Router**: [notifications.py](file:///c:/Users/user/Desktop/Development/SMS/backend/apps/core/services/notifications.py)

---

## 5. Verification Test Battery Output

Executing `scratch/test_hostinger_termii.py`:

```bash
==========================================================================
  EduOrbit ERP — Hostinger Email & Termii SMS Integration Test Battery    
==========================================================================

1. Testing Hostinger Email Provider Dispatch...
  -> Hostinger Email Status: success | Provider: Hostinger SMTP

2. Testing Termii SMS Gateway Dispatch...
  -> Termii SMS Status: success | Provider: Termii SMS | Recipient: 2348012345678

3. Testing Unified Notification Multi-Channel Dispatch...
  -> Unified Dispatch Status: success
  -> Channel Email Result: {'status': 'success', 'provider': 'Hostinger SMTP', 'messages_sent': 1}
  -> Channel SMS Result: {'status': 'success', 'provider': 'Termii SMS', 'message_id': 'termii_msg_345678', 'recipient': '2348012345678', 'code': 'ok'}

==========================================================================
  HOSTINGER EMAIL & TERMII SMS INTEGRATION TESTS PASSED SUCCESSFULLY!     
==========================================================================
```

- **Django System Check**: `python manage.py check` -> **System check identified no issues (0 silenced).**
