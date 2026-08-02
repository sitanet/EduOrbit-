# Phase 12.4.3D - Employee Submission Engine
## Quick Reference Card

**Status:** ✅ COMPLETE | **Date:** August 1, 2026 | **Django Server:** Running

---

## 🚀 WHAT'S NEW

### New API Endpoint
```
POST /hr/api/v1/onboarding/submit/
Body: {"draft_id": "uuid"}
→ Creates full employee record from wizard draft
```

### New Service Method
```python
from backend.apps.hr.services.employee import EmployeeService

employee = EmployeeService.create_employee_from_onboarding_draft(
    tenant=tenant,
    draft=draft,
    actor_person=hr_admin_person
)
```

### New Utility
```python
from backend.apps.hr.utils.encryption import StatutoryPIIEncryption

encrypted = StatutoryPIIEncryption.encode("12345678901")
plaintext = StatutoryPIIEncryption.decode(encrypted)
```

---

## 📁 FILES CHANGED

### Modified (3 files)
1. `backend/apps/hr/services/employee.py` - New method (+267 lines)
2. `backend/apps/hr/api/kyc_views.py` - New endpoint (+128 lines)
3. `backend/apps/hr/api/urls.py` - Route registration (+2 lines)

### Created (2 files)
1. `backend/apps/hr/utils/encryption.py` - PII encoding utility
2. `backend/apps/hr/utils/__init__.py` - Package marker

---

## ✅ WHAT IT DOES

### Wizard Submission Flow
```
User completes Steps 1-3 → Clicks Submit → API Validates Draft
→ Creates Person → Creates User → Assigns Role → Creates Employee
→ Seeds Tasks → Logs Audit → Sends Notification → Returns Success
```

### Data Captured
- ✅ **Step 1:** Personal info, NIN, BVN (with Dojah verification)
- ✅ **Step 2:** Job title, department, employment dates
- ✅ **Step 3:** Banking, Tax ID, Pension, NHF, NHIS, NSITF
- ⏳ **Steps 4-8:** Backend ready, UI pending (Phase 12.4.4)

---

## 🔐 VALIDATION RULES

### STRICT (Will fail submission)
- ❌ Draft not marked complete (`is_completed = False`)
- ❌ No KYC verification (neither NIN nor BVN verified)
- ❌ Missing: first_name, last_name, dob, job_title
- ❌ Duplicate email address

### SOFT (Uses defaults)
- ⚠️ Missing department → defaults to "General"
- ⚠️ Missing salary_grade → defaults to "grade_1"
- ⚠️ Missing date_employed → uses today's date

---

## 🧪 TESTING

### Quick Manual Test
1. Navigate to: `http://localhost:8000/hr/admin/onboarding/wizard/`
2. Complete Step 1 (use real NIN for Dojah verification)
3. Complete Step 2 (employment details)
4. Complete Step 3 (banking & statutory)
5. Open browser console
6. Run JavaScript:
```javascript
fetch('/hr/api/v1/onboarding/submit/', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({draft_id: 'YOUR_DRAFT_ID_HERE'})
})
.then(r => r.json())
.then(console.log)
```

### Expected Success Response
```json
{
    "status": "success",
    "employee_number": "EMP-ABC123",
    "username": "john.doe",
    "email": "john.doe@eduorbit.com"
}
```

---

## 🐛 TROUBLESHOOTING

### Error: "Tenant context required"
**Cause:** TenantMiddleware not setting request.tenant  
**Fix:** Ensure logged in as user with tenant assignment

### Error: "KYC verification missing"
**Cause:** Neither NIN nor BVN verified via Dojah  
**Fix:** Click "Verify NIN" button in Step 1 before submitting

### Error: "Draft not marked as completed"
**Cause:** Draft.is_completed = False  
**Fix:** Ensure wizard reached Step 8 OR manually set in database

### Error: "Duplicate email address"
**Cause:** Email already used by another employee  
**Fix:** Use unique email or delete existing employee

---

## 📊 DATABASE TABLES AFFECTED

### Records Created (per submission)
- ✅ 1x `Person` (demographics)
- ✅ 1x `User` (Django auth)
- ✅ 1x `TenantMembership` (RBAC role)
- ✅ 1x `PersonRole` (staff role)
- ✅ 1x `EmployeeProfile` (HR data)
- ✅ 1x `StaffProfile` (academic system)
- ✅ 1x `OrgAssignmentHistory` (organizational tracking)
- ✅ 5x `OnboardingTask` (post-hire tasks)
- ✅ 1x `HRAuditLog` (compliance audit)

**Total:** 13 database records per employee

---

## 🔍 VERIFICATION QUERIES

### Check Employee Created
```sql
SELECT employee_number, person_id, job_title, status
FROM hr_employeeprofile
WHERE created_at > NOW() - INTERVAL '1 hour'
ORDER BY created_at DESC LIMIT 10;
```

### Check User Account
```sql
SELECT u.username, u.email, u.is_active, p.first_name, p.last_name
FROM identity_user u
JOIN people_person p ON p.user_id = u.id
WHERE u.date_joined > NOW() - INTERVAL '1 hour';
```

### Check Audit Log
```sql
SELECT event_type, model_affected, new_values, created_at
FROM hr_hrauditlog
WHERE event_type = 'employee.onboarded'
ORDER BY created_at DESC LIMIT 10;
```

---

## 📞 QUICK CONTACTS

### For Bugs
- Check Django console: Look for `ERROR:` or `Traceback`
- Check browser console: Look for failed API calls (red text)
- Check database: Verify records created

### For Questions
- **Technical:** Read `PHASE12_4_3D_IMPLEMENTATION_SUMMARY.md`
- **Architecture:** Read `PHASE12_4_3D_REPOSITORY_AUDIT_REPORT.md`
- **Overview:** Read `PHASE12_4_3D_EXECUTIVE_SUMMARY.md`

---

## ⚠️ KNOWN ISSUES

1. **Base64 ≠ Encryption** - PII stored with encoding, not true encryption (Phase 12.5)
2. **Steps 4-8 UI Missing** - Backend ready, frontend pending (Phase 12.4.4)
3. **No "Submit" Button** - JavaScript integration needed in wizard Step 8

---

## 🎯 NEXT STEPS

### TODAY
1. ✅ Implementation complete
2. ⏳ Manual testing
3. ⏳ Fix any bugs found

### THIS WEEK
1. Add "Submit" button to wizard
2. Write unit tests
3. Deploy to staging

### NEXT WEEK
1. Implement Steps 4-8 UI
2. Real encryption (Phase 12.5)
3. Document upload (Phase 12.4.6)

---

**Quick Start:** Django server is already running. Navigate to `/hr/admin/onboarding/wizard/` and test!

**Status:** ✅ READY FOR TESTING  
**Server:** http://localhost:8000  
**Endpoint:** POST /hr/api/v1/onboarding/submit/
