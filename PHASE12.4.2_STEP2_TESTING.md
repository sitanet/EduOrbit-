# PHASE 12.4.2 — STEP 2 TESTING GUIDE

**READY FOR TESTING** ✅

---

## 🚀 Quick Test (5 Minutes)

### Start Server:
```bash
cd backend
python manage.py runserver
```

### Navigate to:
```
http://localhost:8000/hr/admin/onboarding/wizard/
```

### Test Sequence:

**1. Step 1 (Existing)**
- Fill in: First Name, Last Name, DOB, Gender
- Click "Next Step" → Should go to Step 2 ✅

**2. Step 2 (New)**
- Should see "Step 2: Employment Details" header
- Fill required fields:
  - Date Employed: Select today's date
  - Job Title: Type "Senior Teacher"
  - Department: Select "Academics"
  - Position: Select "Teacher"
  - Employment Type: Leave as "Full-Time"
  - Employment Status: Leave as "Active"
  - Confirmation Status: Leave as "Probation"
  - Campus: Leave as "Main Campus"
  - Work Location: Type "Building A, Room 101"

**3. Navigation Test**
- Click "Previous Step" → Should return to Step 1 ✅
- Click "Next Step" from Step 1 → Should go back to Step 2 ✅
- Click progress bar "Step 1" → Should jump to Step 1 ✅
- Click progress bar "Step 2" → Should jump to Step 2 ✅
- Click progress bar "Step 3" → Should show alert "not yet implemented" ✅

**4. Validation Test**
- On Step 2, clear "Job Title" field
- Click "Next Step" → Should show alert "Please fill in all required fields" ✅
- Fill "Job Title" again
- Click "Next Step" → Should show "Steps 3-8 coming soon!" message ✅

**5. Auto-Save Test**
- Wait 5 seconds
- Check browser DevTools → Network tab
- Should see POST to `/hr/api/v1/onboarding/draft/auto-save/` ✅
- Should include both Step 1 and Step 2 data in payload ✅

**6. Browser Refresh Test**
- Press F5 to refresh page
- Should return to Step 1 or Step 2 (depending on last step)
- All fields should retain their values ✅

**7. Keyboard Navigation**
- Press CTRL+Right Arrow → Should navigate forward ✅
- Press CTRL+Left Arrow → Should navigate backward ✅
- Press CTRL+S → Should show "✓ Draft Saved!" ✅
- Press ESC → Should show exit confirmation ✅

---

## 🐛 Expected Behaviors

### ✅ Working:
- Step 1 → Step 2 navigation
- Step 2 → Step 1 navigation
- Validation on both steps
- Auto-save every 5 seconds
- Browser refresh recovery
- Keyboard shortcuts
- Progress bar clicks (Steps 1-2)
- Dojah NIN/BVN verification (Step 1)

### ⚠️ Not Yet Implemented:
- Steps 3-8 (coming next)
- Employee creation (Phase 12.4.3)
- Document upload (Step 6)
- Final submission (Step 8)

---

## 🧪 Console Checks

Open browser DevTools (F12) → Console tab

### Expected Messages:
```
✓ EduOrbit HR Onboarding Wizard initialized (Phase 12.4.2 - Steps 1-2)
```

### Should NOT See:
- ❌ Any JavaScript errors
- ❌ "Uncaught" errors
- ❌ "undefined" variable warnings

---

## 📱 Mobile Test

### Resize browser to 375px width (mobile)

**Expected**:
- Form fields stack vertically ✅
- Progress bar scrolls horizontally ✅
- All buttons accessible ✅
- Dark mode renders correctly ✅

---

## 🎯 Success Criteria

**Step 2 passes if**:
- ✅ All 17 form fields render correctly
- ✅ Required field validation works
- ✅ Navigation between Steps 1-2 works
- ✅ Auto-save includes Step 2 data
- ✅ Browser refresh recovers all data
- ✅ No JavaScript console errors
- ✅ Dark mode colors correct
- ✅ Mobile responsive layout works
- ✅ Dojah integration still works
- ✅ Steps 3-8 properly blocked

---

## 🔧 Quick Fixes

### If validation doesn't work:
- Check browser console for errors
- Verify all input IDs match JavaScript
- Clear browser cache and refresh

### If auto-save fails:
- Check Network tab for 500 errors
- Verify `/hr/api/v1/onboarding/draft/auto-save/` endpoint exists
- Check Django server logs

### If navigation broken:
- Clear localStorage: `localStorage.clear()`
- Refresh page
- Start from Step 1

---

## ✅ Ready for Step 3

Once Step 2 testing passes, proceed to implement:

**Step 3: Bank & Statutory Information**
- Bank Name
- Account Number
- BVN (pre-filled from Step 1)
- Tax ID
- Pension details
- NHF/NHIS/NSITF numbers

---

**TEST STEP 2 NOW** → Then implement Step 3! 🚀
