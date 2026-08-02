# PHASE 12.4.1 — QUICK TEST EXECUTION GUIDE

**⚡ START TESTING NOW**: Follow this streamlined checklist

---

## 🎯 Critical Path Tests (30 Minutes)

### 1. Load & Inspect (5 min)
```
✓ Navigate to: http://localhost:8000/hr/admin/onboarding/wizard/
✓ Open DevTools Console (F12)
✓ Check: Zero JavaScript errors
✓ Check: Page loads successfully
✓ Check: Console log shows: "✓ EduOrbit HR Onboarding Wizard initialized (Phase 12.4.1)"
```

### 2. Navigation Functions (10 min)
```
✓ Click "Next Step →" button
  → Expected: Alert "Please fill in all required fields (marked with *)"
  
✓ Fill required fields:
  - First Name: Natasha
  - Last Name: Romanoff
  - Date of Birth: 1992-06-15
  - Gender: Female (default)
  
✓ Click "Next Step →" again
  → Expected: Green message "⚡ Step 1 Validated. Steps 2-8 coming in Phase 12.4.2!"
  
✓ Check "Previous Step" button
  → Expected: Disabled (opacity-50, cursor-not-allowed)
  
✓ Click Step 2 in progress bar
  → Expected: Alert "Step 2 is not yet implemented. Coming in Phase 12.4.2!"
```

### 3. Dojah KYC Integration (5 min)
```
✓ Enter NIN: 12345678901
✓ Click "⚡ Verify NIN"
  → Expected: Badge changes to "✅ Verified" (green)
  → Expected: Result card appears with mock data
  
✓ Enter BVN: 22345678901
✓ Click "⚡ Verify BVN"
  → Expected: Badge changes to "✅ Verified" (green)
  → Expected: Result card appears
```

### 4. Auto-Save (5 min)
```
✓ Wait 5 seconds after page load
✓ Check Network tab
  → Expected: POST to /hr/api/v1/onboarding/draft/auto-save/
  → Expected: Indicator shows "⚡ Saved at HH:MM:SS"
  
✓ Click "💾 Save Draft" button
  → Expected: Green "✓ Draft Saved!" appears for 2 seconds
  
✓ Refresh page (F5)
  → Expected: Console shows "Draft recovered: {uuid}"
  → Expected: Form values persist
```

### 5. Keyboard Navigation (5 min)
```
✓ Press CTRL+S
  → Expected: "✓ Draft Saved!" appears
  
✓ Press ESC
  → Expected: Confirm dialog "Exit wizard? Your progress will be saved."
  → Click Cancel to stay
  
✓ Press CTRL+Right Arrow
  → Expected: Next step message (since Step 2 not implemented)
  
✓ Press TAB repeatedly
  → Expected: Focus moves through form fields in order
```

---

## 🔍 JavaScript Quality Checks (10 Minutes)

### Console Inspection
```javascript
// Open DevTools Console, run these checks:

// 1. Check for errors
console.log('Errors:', performance.getEntriesByType('navigation'));

// 2. Check variables defined
console.log('currentStep:', typeof currentStep); // → "number"
console.log('draftId:', typeof draftId); // → "object" (null) or "string"
console.log('totalSteps:', typeof totalSteps); // → "number"

// 3. Check functions defined
console.log('showStep:', typeof showStep); // → "function"
console.log('goToStep:', typeof goToStep); // → "function"
console.log('nextStep:', typeof nextStep); // → "function"
console.log('prevStep:', typeof prevStep); // → "function"
console.log('validateStep:', typeof validateStep); // → "function"

// 4. Check localStorage
console.log('Draft ID:', localStorage.getItem('eduorbit_onboarding_draft_id'));
console.log('Current Step:', localStorage.getItem('eduorbit_onboarding_current_step'));

// 5. Test function calls manually
showStep(1);  // Should show step 1
updateProgress();  // Should update progress bar
validateStep(1);  // Should return true (if fields filled)
```

---

## 🌐 Browser Compatibility (20 Minutes)

### Chrome
- [ ] Open in Chrome
- [ ] Run critical path tests
- [ ] Check console: zero errors
- [ ] Take screenshot

### Firefox
- [ ] Open in Firefox
- [ ] Run critical path tests
- [ ] Check console: zero errors
- [ ] Take screenshot

### Edge
- [ ] Open in Edge
- [ ] Run critical path tests
- [ ] Check console: zero errors
- [ ] Take screenshot

### Responsive (Mobile)
- [ ] Resize to 375px width (DevTools Device Mode)
- [ ] Check form fields stack vertically
- [ ] Check progress bar scrolls horizontally
- [ ] Take screenshot

---

## 🔒 Security Quick Checks (15 Minutes)

### XSS Test
```
1. Enter in First Name: <script>alert('XSS')</script>
2. Wait for auto-save
3. Refresh page
4. Expected: No alert fires, text appears as-is
```

### CSRF Check
```
1. Open backend/apps/hr/api/kyc_views.py
2. Verify line 8: @method_decorator(csrf_exempt, name='dispatch')
3. Verify line 22: @method_decorator(csrf_exempt, name='dispatch')
4. Verify line 36: @method_decorator(csrf_exempt, name='dispatch')
5. Verify line 47: @method_decorator(csrf_exempt, name='dispatch')
```

### Authentication Test
```
1. Logout from system
2. Navigate to http://localhost:8000/hr/admin/onboarding/wizard/
3. Expected: Redirect to login page
4. Login again
5. Expected: Wizard loads successfully
```

---

## ⚡ Performance Benchmarks (10 Minutes)

### Page Load
```
1. Open DevTools → Performance tab
2. Reload page
3. Check "Load" event timing
4. Expected: < 2 seconds
```

### DOM Size
```javascript
// In console:
document.querySelectorAll('*').length
// Expected: < 1500 nodes
```

### Auto-Save Latency
```
1. Open DevTools → Network tab
2. Wait for auto-save request
3. Check timing for /hr/api/v1/onboarding/draft/auto-save/
4. Expected: < 500ms
```

### Memory Usage
```
1. Open DevTools → Memory tab
2. Take heap snapshot after page load
3. Wait 5 minutes
4. Take second heap snapshot
5. Expected: < 5MB growth
```

---

## 🐛 Regression Tests (10 Minutes)

### Existing Features Still Work
```
✓ Navigate to /hr/dashboard/
  → Expected: Dashboard loads

✓ Navigate to /hr/admin/directory/
  → Expected: Directory loads
  → Expected: "Add Staff Member (Enterprise Wizard)" link present

✓ Click wizard link
  → Expected: Navigates to wizard, loads successfully

✓ Test NIN verification again
  → Expected: Still works (backend unchanged)

✓ Test BVN verification again
  → Expected: Still works (backend unchanged)
```

---

## 📊 Pass/Fail Criteria

### PASS ✅
- Zero JavaScript console errors
- All navigation functions work
- Step 1 validation works
- Dojah KYC integration preserved
- Auto-save persists data
- Keyboard shortcuts work
- Browser compatibility confirmed
- Performance benchmarks met
- Zero regression failures

### FAIL ❌
- Any JavaScript errors
- Navigation buttons broken
- Validation not working
- KYC integration broken
- Auto-save not persisting
- Security vulnerabilities found
- Performance below threshold
- Regression failures detected

---

## 🚨 Common Issues & Fixes

### Issue: "currentStep is not defined"
**Fix**: Check line ~170 in onboarding_wizard.html
```javascript
let currentStep = 1;  // Must be at top of <script>
```

### Issue: Auto-save not working
**Check**:
1. Network tab shows request?
2. Response has draft_id?
3. localStorage updated?

### Issue: Progress bar not updating
**Check**:
1. updateProgress() called in showStep()?
2. CSS classes applied correctly?

### Issue: Keyboard shortcuts not working
**Check**:
1. Event listener registered on DOMContentLoaded?
2. e.preventDefault() called?

---

## 📝 Test Results Template

Copy this to PHASE12.4.1_TEST_RESULTS.md:

```markdown
# PHASE 12.4.1 TEST RESULTS

**Tested By**: [Your Name]
**Date**: July 30, 2026
**Browser**: Chrome 126 / Firefox 128 / Edge 126
**Environment**: Local Dev Server

## Summary
- Total Tests: 50
- Passed: __
- Failed: __
- Blocked: __
- Pass Rate: __%

## Critical Path Results
- [ ] ✅ Page loads without errors
- [ ] ✅ Navigation functions work
- [ ] ✅ Step 1 validation works
- [ ] ✅ Dojah KYC preserved
- [ ] ✅ Auto-save works
- [ ] ✅ Keyboard navigation works

## Defects Found
### Priority 1 (Blocker)
(None / List here)

### Priority 2 (Critical)
(None / List here)

### Priority 3 (Major)
(None / List here)

### Priority 4 (Minor)
(None / List here)

## Evidence
- Screenshots: [Attach here]
- Console logs: [Paste here]
- Network traces: [Attach here]
- Performance metrics: [Paste here]

## Recommendation
[ ] ✅ PASS - Ready for Phase 12.4.2
[ ] ❌ FAIL - Defects must be fixed first
```

---

## 🎯 Quick Decision Matrix

| Scenario | Action |
|----------|--------|
| Zero errors, all tests pass | ✅ Proceed to Phase 12.4.2 |
| Minor UI issues only | ✅ Proceed, document issues |
| Validation broken | ❌ Fix before proceeding |
| KYC integration broken | ❌ Fix before proceeding |
| Auto-save not working | ❌ Fix before proceeding |
| Performance below 50% | ❌ Optimize before proceeding |
| JavaScript errors present | ❌ Fix before proceeding |

---

## 🚀 Ready to Start?

1. **Start Django server**:
   ```bash
   cd backend
   python manage.py runserver
   ```

2. **Login as HR Admin**:
   - Navigate to http://localhost:8000/login/
   - Use credentials with hr_admin role

3. **Navigate to wizard**:
   - Go to http://localhost:8000/hr/admin/onboarding/wizard/

4. **Open DevTools**:
   - Press F12
   - Switch to Console tab

5. **Follow Critical Path Tests** (above)

6. **Document results** in PHASE12.4.1_TEST_RESULTS.md

---

**ESTIMATED TIME**: 1.5 hours for complete testing

**GOAL**: 95%+ pass rate, zero JavaScript errors, zero regressions

**NEXT PHASE**: Phase 12.4.2 (Steps 2-8 Implementation) - Only after this passes!

---

**END OF QUICK TEST GUIDE**
