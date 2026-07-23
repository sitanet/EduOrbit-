# EduOrbit Identity & Access Management (IAM) System Documentation

This document describes the structure, authentication flows, and dynamic authorization engine for the **identity** module.

---

## 1. IAM Architecture & User Models

### Custom User Model
The `User` model is global (stored at the platform level, inheriting from `PlatformBaseModel` and `AbstractBaseUser`) to allow users to span multiple school tenants or have administrative platform roles. 

### Multi-Tenant Membership mapping
```
[ User (Global) ]
       │
       ▼ (Many-to-Many via TenantMembership)
[ TenantMembership (Tenant-scoped) ] ──> References [ Role (Tenant or Platform scoped) ]
```

---

## 2. Authentication Flow

```
[ Client Request ] ──> [ IdentityService.authenticate_user() ]
                             │
                             ├─> [ Check locks & limits ]
                             ├─> [ Resolve method via IAuthenticationProvider ]
                             │         ├── PasswordProvider
                             │         └── OtpProvider
                             ▼
                    [ Generate Session & tokens ]
```

- **MFA Challenge**: If `mfa_enabled` is set, a 2FA OTP verification is requested. Pluggable TOTP keys are verified against `MfaAuthenticator`.

---

## 3. Authorization Matrix & Permissions
- Permissions are represented by specific metadata codes (e.g. `students.create`, `hostels.view`).
- Role assignment and permission checks are resolved dynamically:
  ```python
  AuthorizationService.check_user_permission(user, "students.create", tenant_id)
  ```

---

## 4. REST APIs Mapping
The endpoints are mounted under `/api/v1/auth/`:
- `POST /auth/login/`: Validates credentials, sets up session, and issues token parameters.
- `POST /auth/logout/`: Revokes access token credentials.
- `POST /auth/refresh/`: Evaluates refresh tokens to rotate active authorization parameters.
- `GET /auth/sessions/`: Lists active devices.

---

## 5. Security & Risk Analysis Considerations
- **Password History**: Restricts reuse against the last 5 passwords by comparing encoded pbkdf2/argon2 hashes (avoiding MD5!).
- **Impossible Travel**: Simple risk detection flagging logins from unknown countries or matching new device fingerprints.
