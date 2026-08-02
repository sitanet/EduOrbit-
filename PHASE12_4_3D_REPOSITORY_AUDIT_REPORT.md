# Phase 12.4.3D – Repository Audit Report
## Employee Submission Engine Implementation

**Date:** August 1, 2026  
**Audit Scope:** Existing implementations for employee onboarding submission  
**Objective:** Identify existing logic to avoid duplication and build the final submission endpoint

---

## 1. REPOSITORY AUDIT FINDINGS

### 1.1 EmployeeProfile Model
**Location:** `backend/apps/hr/models/employee.py`

**Key Fields:**
- `person` - OneToOne to Person (demographics)
- `employee_number` - Unique identifier (auto-generated)
- `job_title`, `salary_grade`, `status`, `employment_type`, `confirmation_status`
- **Banking:** `bank_name`, `account_number`, `account_name`, `sort_code_iban`
- **Statutory Encrypted:** `nin_encrypted`, `bvn_encrypted`, `rsa_pin_encrypted`, `tax_id_encrypted`
- **Statutory Plaintext:** `nhf_number`, `nhis_number`, `nsitf_number`, `pfa_name`
- **KYC Metadata:** `is_nin_verified`, `is_bvn_verified`, `kyc_verification_meta`
- **Organizational:** 7-tier structure (company, campus, division, directorate, department, unit, team)
- **Cost Centre:** `cost_centre` for accounting integration
- **Emergency:** `next_of_kin_name`, `next_of_kin_relationship`, `next_of_kin_phone`

**Status:** ✅ EXISTING - Model is complete with all Step 3 statutory fields added

---

### 1.2 EmployeeService
**Location:** `backend/apps/hr/services/employee.py`

**Existing Method:** `create_employee(tenant, first_name, last_name, email, job_title, ...)`

**What it does:**
1. Validates email uniqueness
2. Creates or finds Person
3. Creates Django User account with username generation
4. Creates TenantMembership with Role assignment
5. Creates PersonRole (staff role)
6. Creates EmployeeProfile with auto-generated employee_number
7. Creates StaffProfile
8. Creates OrgAssignmentHistory
9. Records HRAuditLog entry
10. Publishes `employee.created` domain event

**Limitations:**
- Does NOT accept draft data
- Does NOT handle KYC verification metadata
- Does NOT encrypt statutory PII
- Does NOT validate onboarding draft completeness
- Simple parameter signature (first_name, last_name, email only)

**Status:** ✅ EXISTING but LIMITED - Need enhanced version for onboarding submission

---

### 1.3 OnboardingDraft Model
**Location:** `backend/apps/hr/models/onboarding_draft.py`

**Fields:**
- `draft_id` - UUID (unique identifier)
- `tenant` - TenantBaseModel inheritance
- `version` - Wizard version tracking
- `created_by` - ForeignKey to Person
- `current_step` - Integer (1-8)
- `draft_data` - JSONField (stores all form data)
- `is_completed` - Boolean flag
- `auto_saved_at` - Timestamp

**Status:** ✅ EXISTING - Ready for submission endpoint to consume

---

### 1.4 OnboardingService
**Location:** `backend/apps/hr/services/onboarding.py`

**Existing Methods:**
- `seed_default_tasks(tenant, employee)` - Creates 5 default onboarding tasks
- `toggle_task(tenant, task_id, is_completed, verifier_employee)` - Marks tasks complete

**Status:** ✅ EXISTING - Post-creation onboarding task management

---

### 1.5 Person Model
**Location:** `backend/apps/people/models.py`

**Key Fields:**
- `person_number` - Unique identifier
- `first_name`, `middle_name`, `last_name`, `preferred_name`, `title`
- `gender`, `date_of_birth`, `place_of_birth`, `nationality`, `state_of_origin`
- `local_govt_area`, `religion`, `marital_status`
- `user` - OneToOne to User (optional)

**Status:** ✅ EXISTING - Demographics container

---

### 1.6 RBAC / Role Assignment
**Location:** `backend/apps/identity/models.py`, `backend/apps/identity/services.py`

**Pattern Found:**
```python
# Create or get Role
role_obj, _ = Role.objects.get_or_create(
    tenant=tenant,
    code=f"staff_{tenant.id.hex[:8]}",
    defaults={'name': 'Staff'}
)

# Assign via TenantMembership
TenantMembership.objects.get_or_create(
    user=user,
    tenant=tenant,
    role=role_obj
)
```

**Status:** ✅ EXISTING - Standard pattern for role assignment

---

### 1.7 Audit Logging
**Location:** `backend/apps/hr/models/employee.py`

**HRAuditLog Model:**
- `actor` - Person who performed action
- `event_type` - e.g., "employee.created", "employee.onboarded"
- `model_affected` - e.g., "EmployeeProfile"
- `object_id` - UUID of affected record
- `old_values`, `new_values` - JSONField snapshots
- `ip_address`, `user_agent` - Request metadata
- `reason` - Textual explanation

**Status:** ✅ EXISTING - Comprehensive audit trail

---

### 1.8 Notification Service
**Location:** `backend/apps/core/services/notifications.py`

**UnifiedNotificationService:**
```python
UnifiedNotificationService.send_notification(
    recipient=person.first_name,
    title="Employee Onboarding Complete",
    message="Your account has been created...",
    channels=['in_app', 'email'],
    metadata={'email': person_email}
)
```

**Channels:** in_app, email, sms, push

**Status:** ✅ EXISTING - Multi-channel notification system

---

### 1.9 Payroll Integration
**Location:** `backend/apps/hr/services/payroll.py`

**Finding:** PayrollService does NOT auto-provision on employee creation. It:
- Reads existing EmployeeProfile records
- Matches to SalaryStructure by `salary_grade`
- Generates payslips during `generate_payroll_run()`

**Conclusion:** No automatic payroll provisioning needed. Employee becomes eligible once created.

**Status:** ✅ EXISTING - No changes required

---

### 1.10 Encryption Utilities
**Location:** NOT FOUND

**Finding:** Models have `*_encrypted` fields but NO encryption utility service exists.

**Recommendation:** For Phase 12.4.3D, store encrypted fields as plaintext with comment. Create encryption service in future phase.

**Status:** ⚠️ MISSING - Will implement basic placeholder

---

## 2. MISSING GAPS IDENTIFIED

### Gap 1: Onboarding Submission Endpoint
**What's Missing:** No API endpoint to submit completed wizard draft and create employee

**Solution:** Create `SubmitOnboardingAPIView` in `backend/apps/hr/api/kyc_views.py`

---

### Gap 2: Enhanced Employee Creation from Draft
**What's Missing:** `EmployeeService.create_employee()` doesn't accept draft_data structure

**Solution:** Create `EmployeeService.create_employee_from_onboarding_draft()`

---

### Gap 3: KYC Verification Validation
**What's Missing:** No validation that NIN/BVN were verified before submission

**Solution:** Check `draft_data.kyc_verified` flags in submission endpoint

---

### Gap 4: Statutory PII Storage
**What's Missing:** No encryption implementation for `nin_encrypted`, `bvn_encrypted`, etc.

**Solution:** Store as base64-encoded plaintext with TODO for future encryption service

---

### Gap 5: Domain Event for Onboarding
**What's Missing:** `employee.created` event exists, but no `employee.onboarded` event

**Solution:** Publish new `employee.onboarded` domain event after successful submission

---

## 3. IMPLEMENTATION ARCHITECTURE

### 3.1 Endpoint Design
```
POST /hr/api/v1/onboarding/submit/
Content-Type: application/json

Request Body:
{
    "draft_id": "uuid-string"
}

Response (Success):
{
    "status": "success",
    "employee_number": "EMP-ABC123",
    "employee_id": "uuid",
    "person_number": "PER-XYZ789",
    "username": "john.doe",
    "message": "Employee onboarding completed successfully"
}

Response (Error):
{
    "status": "error",
    "message": "Draft not found or incomplete",
    "validation_errors": [...],
    "missing_steps": [3, 5]
}
```

---

### 3.2 Submission Flow
```
1. Validate draft_id exists and belongs to tenant
2. Check draft.is_completed = True (wizard reached Step 8)
3. Validate KYC verification flags (NIN, BVN)
4. Extract demographics (Step 1) → Create/Update Person
5. Extract employment (Step 2) → Prepare EmployeeProfile fields
6. Extract banking/statutory (Step 3) → Prepare encrypted fields
7. Extract compensation (Step 4) → Set salary_grade
8. Extract emergency (Step 5) → Set next_of_kin fields
9. BEGIN transaction.atomic()
10.   Create Person (if new)
11.   Create User account
12.   Assign TenantMembership role
13.   Create EmployeeProfile with all fields
14.   Create OrgAssignmentHistory
15.   Seed OnboardingTasks
16.   Record HRAuditLog
17.   Mark draft.is_completed = True
18.   Publish employee.onboarded domain event
19. COMMIT
20. Send notification to new employee
21. Return success response
```

---

### 3.3 Transaction Boundary
**CRITICAL:** All database writes wrapped in `transaction.atomic()` to ensure:
- Either ALL records created OR none
- No partial employee state
- Rollback on any validation failure

---

### 3.4 Validation Rules
1. **Draft Completeness:** `current_step >= 8` and `is_completed = True`
2. **KYC Verification:** `draft_data.step1.nin_verified = True` OR `draft_data.step1.bvn_verified = True`
3. **Required Demographics:** first_name, last_name, dob, gender
4. **Required Employment:** job_title, department_name, date_employed
5. **Banking Details:** bank_name, account_number, account_name
6. **Statutory:** tax_id, pfa_name, pension_number

---

## 4. FILES TO MODIFY

### 4.1 Create New Service Method
**File:** `backend/apps/hr/services/employee.py`  
**Method:** `EmployeeService.create_employee_from_onboarding_draft(tenant, draft, actor_person=None)`

**Why:** Handles complex draft_data JSON structure and all 8 wizard steps

---

### 4.2 Create Submission Endpoint
**File:** `backend/apps/hr/api/kyc_views.py`  
**Class:** `SubmitOnboardingAPIView(View)`

**Why:** RESTful endpoint for final wizard submission

---

### 4.3 Update API URLs
**File:** `backend/apps/hr/api/urls.py`  
**Add:** `path('onboarding/submit/', SubmitOnboardingAPIView.as_view(), name='hr_onboarding_submit')`

**Why:** Route registration

---

### 4.4 Create Encryption Placeholder
**File:** `backend/apps/hr/utils/encryption.py` (NEW)  
**Class:** `StatutoryPIIEncryption`

**Why:** Centralized placeholder for future Fernet-based encryption

---

## 5. FILES TO CREATE

### 5.1 Encryption Utility (Placeholder)
**Path:** `backend/apps/hr/utils/encryption.py`

**Purpose:** Base64 encoding placeholder until real encryption implemented

---

### 5.2 Validation Helper
**Path:** `backend/apps/hr/validators/onboarding.py` (if needed)

**Purpose:** Centralized draft validation logic

---

## 6. BLOCKERS & RISKS

### 6.1 Encryption Implementation
**Risk:** Storing PII in plaintext (even encoded) is security risk  
**Mitigation:** Use base64 encoding now, flag with TODO for Django-cryptography integration  
**Timeline:** Address in Phase 12.5 (Security Hardening)

---

### 6.2 Step 4-8 Data Missing
**Risk:** Wizard currently only implements Steps 1-3  
**Mitigation:** Design submission endpoint to accept partial data, default missing fields  
**Timeline:** Steps 4-8 UI implemented in Phase 12.4.4+

---

### 6.3 Email Uniqueness Collision
**Risk:** User enters email already used by another employee  
**Mitigation:** EmployeeValidator.validate_email_uniqueness() already exists  
**Timeline:** Already handled in existing code

---

### 6.4 Transaction Rollback on Notification Failure
**Risk:** Employee created but notification fails  
**Mitigation:** Send notifications AFTER transaction commits (outside atomic block)  
**Timeline:** Design decision - notifications are non-critical

---

## 7. TESTING STRATEGY

### 7.1 Unit Tests
- `test_create_employee_from_draft_success()`
- `test_create_employee_missing_kyc_verification()`
- `test_create_employee_duplicate_email()`
- `test_create_employee_incomplete_draft()`

---

### 7.2 Integration Tests
- `test_submit_onboarding_e2e_happy_path()`
- `test_submit_onboarding_rollback_on_error()`
- `test_submit_onboarding_notification_sent()`

---

### 7.3 Manual Verification
1. Complete wizard Steps 1-3 with real data
2. Submit via API endpoint
3. Verify EmployeeProfile created in database
4. Verify User can log in with generated credentials
5. Verify OnboardingTasks seeded
6. Verify HRAuditLog entry recorded

---

## 8. IMPLEMENTATION CHECKLIST

- [ ] Create `StatutoryPIIEncryption` utility with base64 placeholder
- [ ] Add `EmployeeService.create_employee_from_onboarding_draft()` method
- [ ] Add validation logic for draft completeness
- [ ] Create `SubmitOnboardingAPIView` endpoint
- [ ] Add URL route to `urls.py`
- [ ] Add HRAuditLog entry for "employee.onboarded" event
- [ ] Publish "employee.onboarded" domain event
- [ ] Send welcome notification to new employee
- [ ] Write unit tests for service method
- [ ] Write integration test for endpoint
- [ ] Manual E2E verification
- [ ] Update wizard HTML to call submission endpoint
- [ ] Document API endpoint in Swagger/OpenAPI

---

## 9. SUCCESS CRITERIA

✅ **Draft Submission:** POST to `/hr/api/v1/onboarding/submit/` with draft_id returns employee_number  
✅ **Employee Created:** EmployeeProfile record exists with all Step 1-3 data  
✅ **User Account:** New employee can log in with auto-generated credentials  
✅ **Role Assigned:** TenantMembership exists with "Staff" role  
✅ **Audit Trail:** HRAuditLog contains "employee.onboarded" entry  
✅ **Onboarding Tasks:** 5 default tasks seeded for new employee  
✅ **Notification Sent:** Welcome email/notification delivered  
✅ **Transaction Safety:** Rollback works if any step fails  

---

## 10. NEXT STEPS

**Phase 12.4.3D (THIS PHASE):**
- Implement submission endpoint (Steps 1-3 only)
- Create employee from draft
- Test E2E flow

**Phase 12.4.4 (FUTURE):**
- Implement Step 4 (Compensation & Salary Structure) UI
- Implement Step 5 (Emergency Contacts) UI
- Implement Step 6 (Document Upload) UI
- Implement Step 7 (System Access & Credentials) UI
- Implement Step 8 (Review & Submit) UI

**Phase 12.5 (FUTURE):**
- Replace base64 encoding with Fernet encryption
- Add field-level encryption keys per tenant
- Implement key rotation strategy

---

**Audit Completed:** August 1, 2026  
**Auditor:** Kiro AI  
**Status:** ✅ READY FOR IMPLEMENTATION
