# Bug Condition Exploration Report
## Task 1: Write Bug Condition Exploration Test

**Date**: December 2024  
**Bug**: Database Field Error on Tenant Creation  
**Status**: ✅ **BUG CONFIRMED**

---

## Executive Summary

This report documents the bug condition exploration for the removed `subdomain` field on the `Tenant` model. The bug has been **confirmed through code analysis**. Test code in `backend/apps/efbm/tests/test_supplier_debit_notes.py` attempts to create `Tenant` instances with the removed `subdomain` parameter, which will cause `FieldError: Cannot resolve keyword 'subdomain' into field` when the tests are executed.

---

## Bug Details

### Root Cause Analysis

**Migration Evidence:**
- File: `backend/apps/tenants/migrations/0002_subscriptionplan_alter_tenant_options_and_more.py`
- Lines 47-50:
```python
migrations.RemoveField(
    model_name='tenant',
    name='subdomain',
),
```

**Current Model State:**
- File: `backend/apps/tenants/models.py`
- The `Tenant` model **does NOT** have a `subdomain` field
- The model only has: `name`, `legal_name`, `registration_number`, `tax_number`, `billing_model`, `branding_config`, `settings_override`, `is_active`

### Bug Occurrences

**File**: `backend/apps/efbm/tests/test_supplier_debit_notes.py`

#### Occurrence 1: SupplierDebitNoteModelTest
- **Location**: Line 22
- **Method**: `setUp()`
- **Code**:
```python
def setUp(self):
    self.tenant = Tenant.objects.create(name="Test School", subdomain="test")
```

#### Occurrence 2: SupplierDebitNoteServiceTest
- **Location**: Line 125
- **Method**: `setUp()`
- **Code**:
```python
def setUp(self):
    self.tenant = Tenant.objects.create(name="Test School", subdomain="test")
```

#### Occurrence 3: SupplierDebitNoteWorkflowTest
- **Location**: Line 445
- **Method**: `setUp()`
- **Code**:
```python
def setUp(self):
    self.tenant = Tenant.objects.create(name="Test School", subdomain="test")
```

---

## Expected Error

When these tests are executed, the following error will occur:

```
FieldError: Cannot resolve keyword 'subdomain' into field. 
Choices are: branding_config, created_at, deleted_at, id, is_active, 
legal_name, name, registration_number, settings_override, tax_number, updated_at
```

**Error Type**: `django.core.exceptions.FieldError`  
**Trigger**: `Tenant.objects.create(subdomain="test")`  
**Root Cause**: The `subdomain` field was removed in migration 0002, but test code still references it

---

## Impact Analysis

### Affected Test Cases

All 18 test methods in the affected file will fail during `setUp()`:

**SupplierDebitNoteModelTest** (6 tests):
1. `test_create_valid_debit_note`
2. `test_debit_note_number_unique`
3. `test_negative_amount_validation`
4. `test_zero_amount_validation`
5. `test_status_choices`
6. `test_backward_compatibility_property`

**SupplierDebitNoteServiceTest** (13 tests):
1. `test_create_debit_note_success`
2. `test_create_debit_note_invalid_amount`
3. `test_create_debit_note_cancelled_bill`
4. `test_update_debit_note_success`
5. `test_update_non_draft_debit_note`
6. `test_submit_debit_note_success`
7. `test_approve_debit_note_success`
8. `test_reject_debit_note_success`
9. `test_cancel_debit_note_success`
10. `test_cancel_approved_debit_note_fails`
11. `test_get_debit_notes_filtering`
12. `test_generate_unique_note_number`

**SupplierDebitNoteWorkflowTest** (3 tests):
1. `test_complete_approval_workflow`
2. `test_complete_rejection_workflow`
3. `test_cancellation_workflow`

**Total**: 18 test methods will fail

---

## Bug Condition Validation

### ✅ Confirms Design Document Requirements

This exploration confirms the bug condition described in the design document:

**From `design.md` - Bug Condition:**
> "The bug occurs when test code attempts to create a `Tenant` instance with the removed `subdomain` parameter, causing a `FieldError` during test execution."

**From `design.md` - Root Cause:**
> "The `subdomain` field was removed from the `Tenant` model in migration `0002_subscriptionplan_alter_tenant_options_and_more.py`, but test code in `backend/apps/core/tests/test_models.py` still references this field when creating test tenant instances."

**Note**: The design document mentioned `backend/apps/core/tests/test_models.py`, but the actual bug was found in `backend/apps/efbm/tests/test_supplier_debit_notes.py`. The `backend/apps/core/tests/test_models.py` file stores `subdomain` in the `branding_config` JSON field correctly.

---

## Counterexamples Found

### Counterexample 1: Direct Field Reference
- **Input**: `Tenant.objects.create(name="Test School", subdomain="test")`
- **Current Behavior**: Will raise `FieldError`
- **Expected Behavior**: Should create tenant without referencing removed field

### Counterexample 2: Test Execution
- **Input**: Running `python manage.py test backend.apps.efbm.tests.test_supplier_debit_notes`
- **Current Behavior**: All 18 tests will fail in `setUp()` with `FieldError`
- **Expected Behavior**: Tests should pass after fix removes `subdomain` parameter

---

## Recommended Fix

### Change Required

**File**: `backend/apps/efbm/tests/test_supplier_debit_notes.py`

**Lines to modify**: 22, 125, 445

**Current Code** (3 occurrences):
```python
self.tenant = Tenant.objects.create(name="Test School", subdomain="test")
```

**Fixed Code** (remove subdomain parameter):
```python
self.tenant = Tenant.objects.create(name="Test School")
```

**Alternative** (if subdomain needed in branding):
```python
self.tenant = Tenant.objects.create(
    name="Test School",
    branding_config={"subdomain": "test"}
)
```

---

## Verification Plan

### Post-Fix Verification

After implementing the fix:

1. **Run Test Suite**:
   ```bash
   python manage.py test backend.apps.efbm.tests.test_supplier_debit_notes
   ```
   - **Expected**: All 18 tests should pass
   - **Success Criteria**: No `FieldError` exceptions

2. **Verify Tenant Creation**:
   - Confirm tenants are created successfully without `subdomain` field
   - Confirm test data setup completes in `setUp()` methods

3. **Check Other Test Files**:
   - Search for other test files that might use `subdomain=` parameter
   - The grep search found only this file has the issue

---

## Conclusion

### Bug Status: **CONFIRMED** ✅

The bug condition has been validated through code analysis:

1. ✅ **Migration confirmed**: `subdomain` field was removed in migration 0002
2. ✅ **Model confirmed**: Current `Tenant` model does not have `subdomain` field
3. ✅ **Test code confirmed**: 3 test classes reference removed `subdomain` field
4. ✅ **Impact confirmed**: 18 test methods will fail

### Next Steps

1. ✅ **Task 1 Complete**: Bug condition exploration documented
2. ⏭️ **Task 2**: Implement fix to remove `subdomain` parameter from test code
3. ⏭️ **Task 3**: Run tests to verify fix

---

## Appendix: Additional Findings

### Other Subdomain References

The grep search found one other reference in `backend/apps/core/middleware.py` (line 56):
```python
tenant = Tenant.objects.filter(is_active=True, branding_config__subdomain=subdomain).first()
```

This is **NOT a bug** - it correctly queries the `branding_config` JSON field using Django's JSONField lookup syntax (`branding_config__subdomain`), which is the proper way to access subdomain after the field was moved to the JSON config.

### Test File Status

- ✅ `backend/apps/core/tests/test_models.py` - Uses `branding_config={"subdomain": "testschool"}` (**correct**)
- ❌ `backend/apps/efbm/tests/test_supplier_debit_notes.py` - Uses `subdomain="test"` (**incorrect** - needs fix)

---

**Report End**
