# PHASE 12.4.3 — STEP 3 QUICK TESTING GUIDE

**Step 3: Bank & Statutory Information**  
**Estimated Testing Time**: 15-20 minutes

---

## 🚀 QUICK START

1. Navigate to: `/hr/admin/onboarding/wizard/`
2. Complete Step 1 (Personal Information)
3. Complete Step 2 (Employment Details)
4. Click "Next Step" to reach Step 3

---

## ✅ TEST SCENARIOS

### Scenario 1: Happy Path (2 min)

**Steps**:
1. On Step 3, verify BVN is auto-filled from Step 1 ✅
2. Select "Zenith Bank" from Bank Name dropdown
3. Enter Account Number: `0123456789` (10 digits)
4. Enter Account Name: `Natasha Romanoff`
5. Enter Tax ID: `12345678901234` (14 digits)
6. Select "Stanbic IBTC Pension" from PFA dropdown
7. Enter Pension PIN: `PEN/12345/6789`
8. Leave NHF, NHIS, NSITF blank (optional)
9. Click "Next Step"

**Expected Result**:
- ✅ Validation passes
- ✅ Auto-save indicator updates
- ✅ Alert shows "Steps 4-8 coming soon"
- ✅ Remains on Step 3

---

### Scenario 2: Validation Failures (5 min)

#### Test 2A: Missing Required Fields
1. Leave Bank Name empty
2. Click "Next Step"
3. **Expected**: Alert "Please fill in all required fields in Step 3 (marked with *)"

#### Test 2B: Invalid Account Number (Too Short)
1. Fill all required fields
2. Enter Account Number: `012345678` (9 digits)
3. Click "Next Step"
4. **Expected**: Alert "Account Number must be exactly 10 digits (NUBAN format)"

#### Test 2C: Invalid Account Number (Letters)
1. Enter Account Number: `012ABC5678`
2. Click "Next Step"
3. **Expected**: Alert "Account Number must be exactly 10 digits (NUBAN format)"

#### Test 2D: Invalid Tax ID (Too Short)
1. Fill Account Number correctly
2. Enter Tax ID: `123456789` (9 digits)
3. Click "Next Step"
4. **Expected**: Alert "Tax Identification Number (TIN) must be 10-14 digits"

#### Test 2E: Invalid Tax ID (Letters)
1. Enter Tax ID: `12345ABC01`
2. Click "Next Step"
3. **Expected**: Alert "Tax Identification Number (TIN) must be 10-14 digits"

---

### Scenario 3: Navigation (3 min)

#### Test 3A: Forward Navigation from Step 2
1. Go to Step 2
2. Click "Next Step"
3. **Expected**: 
   - Step 2 validates
   - Navigates to Step 3
   - BVN auto-filled
   - Focus on Bank Name dropdown

#### Test 3B: Backward Navigation to Step 2
1. On Step 3
2. Click "Previous Step"
3. **Expected**:
   - No validation required
   - Navigates to Step 2
   - Step 2 data preserved

#### Test 3C: Backward Navigation to Step 1
1. On Step 3
2. Click Step 1 circle in progress bar
3. **Expected**:
   - No validation required
   - Navigates to Step 1
   - Step 1 data preserved

#### Test 3D: Progress Bar
1. Navigate to Step 3
2. **Expected Progress Bar**:
   - Step 1: ✅ Green circle (completed)
   - Step 2: ✅ Green circle (completed)
   - Step 3: 🔵 Indigo circle with ring (active)
   - Steps 4-8: ⚪ Gray circles (future)

---

### Scenario 4: BVN Auto-Fill (2 min)

1. Go to Step 1
2. Change BVN to `99999999999`
3. Navigate to Step 3
4. **Expected**: BVN field shows `99999999999`
5. Try to edit BVN field
6. **Expected**: Field is readonly (cursor-not-allowed)
7. Check field styling
8. **Expected**: 
   - Background: `bg-slate-800`
   - Text color: `text-emerald-300`
   - Help text: "Pre-filled from Step 1 verification"

---

### Scenario 5: Auto-Save (3 min)

1. Fill all Step 3 fields
2. Wait 5 seconds
3. **Expected**: Auto-save indicator updates "⚡ Saved at [time]"
4. Click "💾 Save Draft" button
5. **Expected**: 
   - Indicator changes to "✓ Draft Saved!" (green)
   - After 2 seconds, reverts to normal
6. Open browser console
7. Check localStorage
8. **Expected**: Keys present:
   - `eduorbit_onboarding_draft_id`
   - `eduorbit_onboarding_current_step`

---

### Scenario 6: Dropdown Options (2 min)

#### Test 6A: Bank Name Dropdown
1. Click Bank Name dropdown
2. **Expected**: 19 Nigerian banks listed
3. Verify options include:
   - Access Bank
   - GTBank
   - Zenith Bank
   - UBA
   - First Bank

#### Test 6B: PFA Dropdown
1. Click PFA dropdown
2. **Expected**: 18 PFAs listed
3. Verify options include:
   - ARM Pension Managers
   - Stanbic IBTC Pension
   - Premium Pension
   - Trustfund Pensions

---

### Scenario 7: UI/UX (3 min)

#### Test 7A: Mobile Layout (375px)
1. Resize browser to 375px width
2. **Expected**:
   - All fields stack vertically (single column)
   - Progress bar scrolls horizontally
   - No horizontal overflow
   - All text readable

#### Test 7B: Desktop Layout (1920px)
1. Resize browser to 1920px width
2. **Expected**:
   - Banking section: 3 columns
   - Tax section: 2 columns
   - Pension section: 2 columns
   - Statutory section: 3 columns

#### Test 7C: Dark Mode
1. Check field styling
2. **Expected**:
   - Input background: Dark (`bg-slate-900`)
   - Borders: `border-slate-800`
   - Labels: Light gray (`text-slate-300`)
   - Help text: Subtle gray (`text-slate-500`)
   - Readonly BVN: Different background (`bg-slate-800`)

---

### Scenario 8: Accessibility (2 min)

#### Test 8A: Tab Navigation
1. Press Tab repeatedly
2. **Expected**:
   - Focus moves through fields in order:
     1. Bank Name dropdown
     2. Account Number
     3. Account Name
     4. (Skips readonly BVN)
     5. Tax ID
     6. PFA dropdown
     7. Pension PIN
     8. NHF Number
     9. NHIS Number
     10. NSITF Number
     11. Previous Step button
     12. Next Step button

#### Test 8B: Keyboard Shortcuts
1. Press **CTRL+Right Arrow**
2. **Expected**: Same as clicking "Next Step" (validates first)
3. Press **CTRL+Left Arrow**
4. **Expected**: Same as clicking "Previous Step"
5. Press **CTRL+S**
6. **Expected**: Manual draft save

---

### Scenario 9: Dojah Regression (2 min)

1. Go to Step 1
2. Click "⚡ Verify NIN" button
3. **Expected**: 
   - Badge changes to "✅ Verified"
   - Result card appears
4. Click "⚡ Verify BVN" button
5. **Expected**:
   - Badge changes to "✅ Verified"
   - Result card appears
6. Check browser console
7. **Expected**: No JavaScript errors

---

### Scenario 10: Browser Refresh (2 min)

1. Fill Step 3 fields
2. Wait for auto-save (5 seconds)
3. Refresh browser (F5)
4. **Expected**:
   - Page reloads to Step 1
   - Draft ID persists in localStorage
   - **Note**: Full data restoration not yet implemented (future phase)

---

## 🐛 BUG REPORTING

If you find any issues, report with:
1. **Steps to reproduce**
2. **Expected behavior**
3. **Actual behavior**
4. **Browser** (Chrome, Firefox, Safari, Edge)
5. **Screen size** (if layout issue)
6. **Console errors** (if any)

---

## ✅ CERTIFICATION CRITERIA

For Step 3 to pass certification (≥ 95/100):
- ✅ All required field validation working
- ✅ NUBAN format validation (10 digits)
- ✅ Tax ID format validation (10-14 digits)
- ✅ BVN auto-fill from Step 1
- ✅ Navigation between Steps 1, 2, 3 working
- ✅ Auto-save includes all 9 Step 3 fields
- ✅ Dojah KYC (Steps 1) still working
- ✅ No JavaScript errors
- ✅ No console errors
- ✅ Mobile responsive
- ✅ Dark mode styling correct
- ✅ Accessibility compliant

---

## 📊 QUICK CHECKLIST

**Critical Tests** (Must Pass):
- [ ] BVN auto-fills from Step 1
- [ ] Empty required fields block navigation
- [ ] Account number validates 10 digits exactly
- [ ] Tax ID validates 10-14 digits
- [ ] Navigation Steps 1 ↔ 2 ↔ 3 works
- [ ] Auto-save includes Step 3 fields
- [ ] Dojah NIN/BVN still works
- [ ] No JavaScript errors

**Important Tests** (Should Pass):
- [ ] Backward navigation requires no validation
- [ ] Progress bar updates correctly
- [ ] Optional fields (NHF, NHIS, NSITF) don't block navigation
- [ ] Mobile layout works
- [ ] Dark mode styling correct
- [ ] Tab navigation skips readonly BVN

**Nice-to-Have Tests**:
- [ ] Help text visible and helpful
- [ ] Dropdown options comprehensive
- [ ] Focus management smooth
- [ ] Keyboard shortcuts work

---

**Estimated Total Testing Time**: 15-20 minutes  
**Pass Criteria**: All Critical + Important tests passing

**END OF TESTING GUIDE**
