# EduOrbit HRMS v1.1.0 — API Reference Guide (`hr_api_documentation.md`)

> **Base URL**: `/hr/api/v1/`  
> **Auth Scheme**: Session / Token Authentication  
> **Version Policy**: `v1` supported for 24 months

---

## 1. KYC Identity Verification Endpoints

### 1.1 NIN Verification
- **Endpoint**: `POST /hr/api/v1/kyc/verify-nin/`
- **Payload**:
  ```json
  { "nin": "12345678901" }
  ```
- **Response (200 OK)**:
  ```json
  {
    "status": "success",
    "is_verified": true,
    "provider": "Dojah Sandbox",
    "data": {
      "full_name": "Natasha Romanoff",
      "dob": "1992-06-15",
      "gender": "Female"
    }
  }
  ```

### 1.2 BVN Verification
- **Endpoint**: `POST /hr/api/v1/kyc/verify-bvn/`
- **Payload**:
  ```json
  { "bvn": "22345678901" }
  ```
- **Response (200 OK)**:
  ```json
  {
    "status": "success",
    "is_verified": true,
    "provider": "Dojah Sandbox"
  }
  ```

### 1.3 Bank Account NUBAN Resolution
- **Endpoint**: `POST /hr/api/v1/kyc/resolve-bank/`
- **Payload**:
  ```json
  { "account_number": "0123456789", "bank_code": "058" }
  ```
- **Response (200 OK)**:
  ```json
  {
    "status": "success",
    "is_resolved": true,
    "data": {
      "account_name": "NATASHA ROMANOFF",
      "bank_name": "GTBank PLC"
    }
  }
  ```

---

## 2. Onboarding Draft Auto-Save Endpoint

- **Endpoint**: `POST /hr/api/v1/onboarding/draft/auto-save/`
- **Payload**:
  ```json
  {
    "draft_id": "optional-uuid",
    "current_step": 2,
    "draft_data": { "first_name": "Natasha", "nin": "12345678901" }
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "status": "success",
    "draft_id": "04a8ecd2-01d9-4eda-b7e0-1f86e060d019",
    "auto_saved_at": "14:15:32"
  }
  ```
