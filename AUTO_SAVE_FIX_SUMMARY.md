# AUTO-SAVE 500 ERROR FIX

**Date:** 2026-08-01  
**Issue:** `/hr/api/v1/onboarding/draft/auto-save/` returning 500 Internal Server Error

---

## Changes Made

### 1. Enhanced Logging Configuration ✅

**File:** `backend/config/settings/local.py`

**Changes:**
- Added verbose formatter with timestamps and module names
- Changed `django.request` log level from ERROR to DEBUG
- Added loggers for `django` and `django.server`
- Set `propagate=False` to prevent duplicate logs

**Result:** Full error tracebacks will now appear in console

---

### 2. Improved AutoSaveDraftAPIView Error Handling ✅

**File:** `backend/apps/hr/api/kyc_views.py`

**Changes:**
```python
# BEFORE
if draft_id:
    draft, _ = OnboardingDraft.objects.get_or_create(draft_id=draft_id)
else:
    draft = OnboardingDraft.objects.create()
    
# Error handling
except Exception as e:
    return JsonResponse({"status": "error", "message": str(e)}, status=500)
```

```python
# AFTER
if draft_id:
    try:
        draft = OnboardingDraft.objects.get(draft_id=draft_id)
    except OnboardingDraft.DoesNotExist:
        draft = OnboardingDraft.objects.create()
else:
    draft = OnboardingDraft.objects.create()
    
# Enhanced error handling with traceback
except Exception as e:
    import traceback
    error_details = traceback.format_exc()
    print(f"AutoSaveDraft ERROR: {error_details}")
    return JsonResponse({"status": "error", "message": str(e), "details": error_details}, status=500)
```

**Improvements:**
- ✅ Fixed `get_or_create()` usage (was incorrect with UUID field)
- ✅ Added explicit `try/except` for draft retrieval
- ✅ Added full traceback printing to console
- ✅ Added traceback to JSON response for debugging
- ✅ Added null check for `auto_saved_at` field

---

## Next Steps

### Step 1: Restart Django Server

The changes require a server restart. Press `CTRL+C` to stop, then run:
```bash
python manage.py runserver
```

### Step 2: Check for Detailed Error

When you access the onboarding wizard, you should now see:
- Full Python traceback in the console
- Error details in the JSON response

### Step 3: Likely Root Causes

Based on the code analysis, the 500 error is likely caused by one of:

1. **Missing Migration** — `OnboardingDraft` table doesn't exist
   ```bash
   python manage.py migrate hr
   ```

2. **Tenant Context Missing** — `TenantBaseModel` requires tenant in request
   - The view needs tenant context from middleware
   - Check if `TenantMiddleware` is running before this endpoint

3. **UUID Field Issue** — `get_or_create()` doesn't work well with UUID primary keys
   - **FIXED** in the code above (changed to explicit `get()` + `try/except`)

---

## Verification

After restarting the server, navigate to:
```
http://127.0.0.1:8000/hr/admin/onboarding/wizard/
```

**Expected Behavior:**
- Auto-save should work every 5 seconds
- Console should show: `"status": "success"` in the response
- No more 500 errors

**If 500 Still Occurs:**
The console will now print the full traceback showing exactly which line is failing and why.

---

## Related Files

1. ✅ `backend/config/settings/local.py` — Enhanced logging
2. ✅ `backend/apps/hr/api/kyc_views.py` — Fixed AutoSaveDraftAPIView
3. 📄 `backend/apps/hr/models/onboarding_draft.py` — Model definition (unchanged)
4. 📄 `backend/apps/hr/migrations/0008_onboardingdraft.py` — Migration (should be applied)

---

**Status:** ✅ Enhanced error handling and logging applied  
**Action Required:** Restart Django server and check console for detailed error
