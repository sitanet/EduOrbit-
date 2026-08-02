# PHASE 12.4.1 — HR ONBOARDING WIZARD TESTING & VALIDATION

**STATUS**: 🔵 **TESTING IN PROGRESS**  
**DATE**: July 30, 2026  
**PHASE**: Testing & Validation Only (No Implementation)  
**SCOPE**: Validate navigation framework implemented in Phase 12.4.1

---

## 🎯 Executive Summary

**OBJECTIVE**: Perform complete validation of the newly implemented HR Onboarding Wizard navigation framework before proceeding to Phase 12.4.2 (Steps 2-8 implementation).

**TESTING SCOPE**:
- ✅ Step navigation functions (showStep, goToStep, nextStep, prevStep)
- ✅ Progress bar management (updateProgress, updateNavigationButtons)
- ✅ Step 1 validation (validateStep for Step 1 only)
- ✅ Auto-save and draft management (saveDraftAuto, loadDraft, clearDraft)
- ✅ Keyboard navigation (ESC, CTRL+S, arrow keys)
- ✅ Browser refresh recovery via localStorage
- ✅ Dojah KYC integration preservation (NIN/BVN verification)
- ✅ Security validation (XSS, CSRF, input sanitization)
- ✅ Performance benchmarks (page load, transitions)
- ✅ Regression testing (no broken existing features)

**CRITICAL CONSTRAINTS**:
- 🚫 Do NOT implement Steps 2-8 (future phase)
- 🚫 Do NOT redesign the wizard UI
- 🚫 Do NOT add new business logic
- 🚫 Do NOT modify backend services (unless verified defect found)
- ✅ Only repair defects discovered during testing
- ✅ Produce evidence for every finding

---

## 📋 Test Scope Matrix

### Files Under Test
| File Path | Purpose | Test Coverage |
|-----------|---------|---------------|
| `backend/templates/hr/admin/onboarding_wizard.html` | Navigation framework JavaScript | 100% |
| `backend/apps/hr/views_web.py` | OnboardingWizardWebView | URL resolution, auth |
| `backend/apps/hr/urls.py` | URL routing | Path resolution |
| `backend/apps/hr/api/kyc_views.py` | KYC API endpoints | Regression only |
| `backend/apps/hr/services/kyc.py` | Dojah provider | Regression only |

---

## 🧪 Test Categories

### 1. STEP NAVIGATION TESTING

#### 1.1 Function Existence
- [ ] `showStep(stepNumber)` defined
- [ ] `goToStep(stepNumber)` defined
- [ ] `nextStep()` defined
- [ ] `prevStep()` defined
- [ ] No JavaScript syntax errors
- [ ] No undefined function references

#### 1.2 Navigation Button Behavior
**Test Case 1.2.1: Previous Button on Step 1**
- **Action**: Load wizard, check prevStepBtn state
- **Expected**: Button disabled, class contains 'opacity-50 cursor-not-allowed'
- **Evidence Required**: Screenshot, console log

**Test Case 1.2.2: Next Button on Step 1**
- **Action**: Load wizard, check nextStepBtn state
- **Expected**: Button enabled, text "Next Step →", class contains 'bg-indigo-600'
- **Evidence Required**: Screenshot, DOM inspection

**Test Case 1.2.3: Next Button Click Without Validation**
- **Action**: Clear required fields, click Next
- **Expected**: Alert "Please fill in all required fields (marked with *)"
- **Evidence Required**: Alert screenshot, no step transition

**Test Case 1.2.4: Next Button Click With Validation**
- **Action**: Fill all required fields, click Next
- **Expected**: Auto-save indicator shows "⚡ Step 1 Validated. Steps 2-8 coming in Phase 12.4.2!"
- **Evidence Required**: Indicator text, indicator class 'text-emerald-400'

#### 1.3 Direct Step Navigation
**Test Case 1.3.1: Click Step 1 in Progress Bar**
- **Action**: Click step 1 circle in progress bar
- **Expected**: Step 1 remains visible, no errors
- **Evidence Required**: Console clean, step-1 display:block

**Test Case 1.3.2: Click Step 2+ in Progress Bar**
- **Action**: Click step 2 circle in progress bar
- **Expected**: Alert "Step 2 is not yet implemented. Coming in Phase 12.4.2!"
- **Evidence Required**: Alert screenshot, step 1 still visible

#### 1.4 Step Visibility Management
**Test Case 1.4.1: Initial Load**
- **Action**: Navigate to /hr/admin/onboarding/wizard/
- **Expected**: Only step-1 visible (display:block), all others hidden
- **Evidence Required**: DOM inspection, querySelectorAll('.wizard-step')

**Test Case 1.4.2: Scroll to Top on Step Transition**
- **Action**: Scroll down, trigger showStep(1)
- **Expected**: Smooth scroll to #onboardingWizardApp container top
- **Evidence Required**: Visual confirmation, scrollIntoView called

**Test Case 1.4.3: Focus First Input**
- **Action**: Call showStep(1)
- **Expected**: After 300ms, #firstNameInput receives focus
- **Evidence Required**: document.activeElement === firstNameInput

---

### 2. PROGRESS BAR TESTING

#### 2.1 Progress Indicator Visual States
**Test Case 2.1.1: Step 1 Active State**
- **Action**: Load wizard (currentStep = 1)
- **Expected**: 
  - Circle: bg-indigo-600, ring-2 ring-indigo-400
  - Label: text-indigo-300
  - Nav: active class present
- **Evidence Required**: Computed styles screenshot

**Test Case 2.1.2: Future Steps State**
- **Action**: Check steps 2-8 styling on initial load
- **Expected**:
  - Circle: bg-slate-800, text-slate-400
  - Label: text-slate-400
  - No active class
- **Evidence Required**: DOM class inspection

#### 2.2 Progress Persistence
**Test Case 2.2.1: Manual Navigation**
- **Action**: Click step 1 indicator after validation
- **Expected**: Step 1 indicator maintains proper state
- **Evidence Required**: updateProgress() called, classes correct

---

### 3. STEP 1 VALIDATION TESTING

#### 3.1 Required Fields Validation
**Test Case 3.1.1: First Name Required**
- **Action**: Clear #firstNameInput, click Next
- **Expected**: Validation alert shown, no step transition
- **Evidence Required**: Alert text, validateStep(1) returns false

**Test Case 3.1.2: Last Name Required**
- **Action**: Clear #lastNameInput, click Next
- **Expected**: Validation alert shown, no step transition
- **Evidence Required**: Alert text, validateStep(1) returns false

**Test Case 3.1.3: Date of Birth Required**
- **Action**: Clear #dobInput, click Next
- **Expected**: Validation alert shown, no step transition
- **Evidence Required**: Alert text, validateStep(1) returns false

**Test Case 3.1.4: Gender Required**
- **Action**: Deselect #genderInput, click Next
- **Expected**: Validation alert shown (gender should have default)
- **Evidence Required**: Default value 'female', validation passes

**Test Case 3.1.5: All Required Fields Present**
- **Action**: Fill firstName, lastName, dob, gender. Click Next
- **Expected**: Validation passes, stepValidationState[1] = true
- **Evidence Required**: No alert, success indicator shown

#### 3.2 Optional Fields
**Test Case 3.2.1: Middle Name Optional**
- **Action**: Leave #middleNameInput empty, click Next
- **Expected**: Validation passes
- **Evidence Required**: No validation error

**Test Case 3.2.2: Marital Status Optional**
- **Action**: Leave #maritalStatusInput default, click Next
- **Expected**: Validation passes
- **Evidence Required**: No validation error

#### 3.3 NIN/BVN Fields (Not Required for Step 1)
**Test Case 3.3.1: NIN Not Required**
- **Action**: Leave #ninInput empty, click Next
- **Expected**: Validation passes (NIN verification is optional)
- **Evidence Required**: No validation error for empty NIN

**Test Case 3.3.2: BVN Not Required**
- **Action**: Leave #bvnInput empty, click Next
- **Expected**: Validation passes (BVN verification is optional)
- **Evidence Required**: No validation error for empty BVN

---

### 4. DOJAH KYC INTEGRATION TESTING

**CRITICAL**: Do NOT modify backend. Only verify existing implementation works.

#### 4.1 NIN Verification Workflow
**Test Case 4.1.1: Valid NIN (Sandbox)**
- **Action**: Enter "12345678901", click "⚡ Verify NIN"
- **Expected**: 
  - AJAX POST to /hr/api/v1/kyc/verify-nin/
  - Response: {status: "success", is_verified: true, provider: "Sandbox"}
  - Badge updates: bg-emerald-500/20, text "✅ Verified"
  - Result card unhidden
- **Evidence Required**: Network tab, console log, DOM changes

**Test Case 4.1.2: Empty NIN**
- **Action**: Clear #ninInput, click "⚡ Verify NIN"
- **Expected**: Function completes, sends empty string to API
- **Evidence Required**: Network request body

**Test Case 4.1.3: Network Error Handling**
- **Action**: Disconnect network, click "⚡ Verify NIN"
- **Expected**: fetch() fails, catch block logs error
- **Evidence Required**: Console error message

#### 4.2 BVN Verification Workflow
**Test Case 4.2.1: Valid BVN (Sandbox)**
- **Action**: Enter "22345678901", click "⚡ Verify BVN"
- **Expected**:
  - AJAX POST to /hr/api/v1/kyc/verify-bvn/
  - Response: {status: "success", is_verified: true, provider: "Sandbox"}
  - Badge updates: bg-emerald-500/20, text "✅ Verified"
  - Result card unhidden
- **Evidence Required**: Network tab, DOM changes

**Test Case 4.2.2: AJAX Response Handling**
- **Action**: Trigger BVN verification, inspect response
- **Expected**: then() chain updates DOM correctly
- **Evidence Required**: Response JSON, DOM mutations

#### 4.3 Backend Regression Test
**Test Case 4.3.1: KYC API Endpoints Exist**
- **Action**: Check backend/apps/hr/api/urls.py
- **Expected**: 
  - path('kyc/verify-nin/', ...)
  - path('kyc/verify-bvn/', ...)
  - path('onboarding/draft/auto-save/', ...)
- **Evidence Required**: File line numbers

**Test Case 4.3.2: Provider Selection Logic**
- **Action**: Check backend/apps/hr/services/kyc.py
- **Expected**: get_kyc_provider() returns DojahKYCProvider if DOJAH_API_KEY exists, else SandboxKYCProvider
- **Evidence Required**: Function source code

---

### 5. AUTO-SAVE & DRAFT MANAGEMENT TESTING

#### 5.1 Auto-Save Functionality
**Test Case 5.1.1: Auto-Save Trigger**
- **Action**: Load wizard, wait 5 seconds
- **Expected**: saveDraftAuto() called via setInterval
- **Evidence Required**: Network request to /hr/api/v1/onboarding/draft/auto-save/

**Test Case 5.1.2: Auto-Save Request Payload**
- **Action**: Fill form data, wait 5 seconds
- **Expected**: POST payload contains:
  ```json
  {
    "draft_id": "uuid-string or null",
    "current_step": 1,
    "draft_data": {
      "first_name": "Natasha",
      "last_name": "Romanoff",
      "dob": "1992-06-15",
      "gender": "female",
      ...
    }
  }
  ```
- **Evidence Required**: Network tab request body

**Test Case 5.1.3: Auto-Save Response Handling**
- **Action**: Observe auto-save response
- **Expected**: 
  - Response: {status: "success", draft_id: "uuid", auto_saved_at: "14:15:00"}
  - draftId variable updated
  - localStorage updated: eduorbit_onboarding_draft_id, eduorbit_onboarding_current_step
  - Indicator text: "⚡ Saved at 14:15:00"
- **Evidence Required**: localStorage inspection, indicator text

#### 5.2 Manual Save
**Test Case 5.2.1: Save Draft Button**
- **Action**: Click "💾 Save Draft" button
- **Expected**:
  - saveDraftManual() calls saveDraftAuto()
  - Indicator shows "✓ Draft Saved!" (green, 2 seconds)
  - Reverts to previous text after timeout
- **Evidence Required**: Indicator state transitions

#### 5.3 Draft Recovery
**Test Case 5.3.1: Browser Refresh Recovery**
- **Action**: 
  1. Fill form, wait for auto-save
  2. Press F5 to refresh page
- **Expected**: 
  - loadDraft() reads localStorage
  - draftId restored
  - currentStep = 1
  - Form values persist (browser auto-fill)
- **Evidence Required**: Console log "Draft recovered: {uuid}", form values unchanged

**Test Case 5.3.2: localStorage Persistence**
- **Action**: Inspect localStorage after auto-save
- **Expected**: 
  - Key: eduorbit_onboarding_draft_id, Value: uuid
  - Key: eduorbit_onboarding_current_step, Value: "1"
- **Evidence Required**: DevTools Application tab screenshot

**Test Case 5.3.3: Clear Draft**
- **Action**: Call clearDraft() in console
- **Expected**: localStorage keys removed, draftId = null
- **Evidence Required**: localStorage empty for these keys

#### 5.4 beforeunload Handler
**Test Case 5.4.1: Save on Exit**
- **Action**: Fill form, close tab (cancel close when prompted)
- **Expected**: beforeunload listener calls saveDraftAuto()
- **Evidence Required**: Network request fires before unload

---

### 6. KEYBOARD NAVIGATION TESTING

#### 6.1 Escape Key
**Test Case 6.1.1: ESC to Exit**
- **Action**: Press ESC key
- **Expected**: confirm() dialog: "Exit wizard? Your progress will be saved."
- **Evidence Required**: Confirm dialog screenshot

**Test Case 6.1.2: ESC Confirm Yes**
- **Action**: Press ESC, click OK in confirm
- **Expected**: 
  - saveDraftManual() called
  - Redirect to {% url "hr_admin_directory" %}
- **Evidence Required**: URL change to /hr/admin/directory/

**Test Case 6.1.3: ESC Confirm No**
- **Action**: Press ESC, click Cancel
- **Expected**: Remain on wizard page
- **Evidence Required**: No redirect, wizard still visible

#### 6.2 CTRL+S / CMD+S
**Test Case 6.2.1: Manual Save Shortcut**
- **Action**: Press CTRL+S (or CMD+S on Mac)
- **Expected**: 
  - e.preventDefault() called
  - saveDraftManual() triggered
  - Indicator shows "✓ Draft Saved!"
- **Evidence Required**: No browser save dialog, indicator updates

#### 6.3 Arrow Keys
**Test Case 6.3.1: CTRL+Right Arrow**
- **Action**: Press CTRL+Right Arrow
- **Expected**: 
  - e.preventDefault() called
  - nextStep() called
  - For Step 1: Shows "Steps 2-8 coming..." message
- **Evidence Required**: Indicator message

**Test Case 6.3.2: CTRL+Left Arrow on Step 1**
- **Action**: Press CTRL+Left Arrow
- **Expected**: 
  - e.preventDefault() called
  - prevStep() called
  - currentStep = 1, no change
- **Evidence Required**: Step remains 1

#### 6.4 Tab Navigation
**Test Case 6.4.1: Tab Through Form Fields**
- **Action**: Press Tab repeatedly from #firstNameInput
- **Expected**: Focus moves: firstName → middleName → lastName → dob → gender → maritalStatus → ninInput → BVN button
- **Evidence Required**: document.activeElement changes correctly

**Test Case 6.4.2: Shift+Tab Reverse**
- **Action**: Focus last field, press Shift+Tab
- **Expected**: Focus moves backward through form
- **Evidence Required**: Reverse tab order

---

### 7. BROWSER COMPATIBILITY TESTING

#### 7.1 Chrome (Latest)
- [ ] All navigation functions work
- [ ] No console errors
- [ ] Auto-save works
- [ ] localStorage works
- [ ] Keyboard shortcuts work

#### 7.2 Firefox (Latest)
- [ ] All navigation functions work
- [ ] No console errors
- [ ] Auto-save works
- [ ] localStorage works
- [ ] Keyboard shortcuts work

#### 7.3 Edge (Latest)
- [ ] All navigation functions work
- [ ] No console errors
- [ ] Auto-save works
- [ ] localStorage works
- [ ] Keyboard shortcuts work

#### 7.4 Responsive Design
**Test Case 7.4.1: Mobile (375px width)**
- **Action**: Resize to 375px width
- **Expected**: 
  - Progress bar horizontally scrollable (overflow-x-auto)
  - Form fields stack vertically
  - Buttons remain accessible
- **Evidence Required**: Screenshot

**Test Case 7.4.2: Tablet (768px width)**
- **Action**: Resize to 768px width
- **Expected**: Grid changes from 3-column to 2-column (md:grid-cols-3 → grid-cols-1)
- **Evidence Required**: Computed grid layout

---

### 8. DARK MODE TESTING

#### 8.1 Color Scheme Validation
**Test Case 8.1.1: Background Colors**
- **Action**: Inspect container backgrounds
- **Expected**: 
  - Main container: bg-slate-900
  - Form fields: bg-slate-950
  - Borders: border-slate-800
- **Evidence Required**: Computed styles

**Test Case 8.1.2: Text Colors**
- **Action**: Inspect text elements
- **Expected**:
  - Headers: text-white
  - Labels: text-slate-300
  - Helper text: text-slate-400
- **Evidence Required**: Contrast ratio ≥ 4.5:1 (WCAG AA)

**Test Case 8.1.3: Button Colors**
- **Action**: Inspect button states
- **Expected**:
  - Primary: bg-indigo-600 hover:bg-indigo-700
  - Disabled: opacity-50
  - Success: bg-emerald-600
- **Evidence Required**: Screenshot, hover states

**Test Case 8.1.4: Badge Colors**
- **Action**: Inspect NIN/BVN badges
- **Expected**:
  - Pending: bg-amber-500/20 text-amber-300
  - Verified: bg-emerald-500/20 text-emerald-300
- **Evidence Required**: Badge state transitions

---

### 9. JAVASCRIPT QUALITY TESTING

#### 9.1 Console Errors
**Test Case 9.1.1: Zero Console Errors**
- **Action**: Load wizard, perform all actions
- **Expected**: No errors, warnings, or syntax issues in console
- **Evidence Required**: Console screenshot (empty errors)

#### 9.2 Undefined Variables
**Test Case 9.2.1: All Variables Declared**
- **Action**: Search code for undeclared variables
- **Expected**: All variables declared with let/const
- **Evidence Required**: Code review, no implicit globals

#### 9.3 Memory Leaks
**Test Case 9.3.1: Event Listener Cleanup**
- **Action**: Check event listeners
- **Expected**: 
  - DOMContentLoaded listener executes once
  - keydown listener registered once
  - beforeunload listener registered once
  - No duplicate listeners
- **Evidence Required**: getEventListeners(document) inspection

**Test Case 9.3.2: setInterval Cleanup**
- **Action**: Check auto-save interval
- **Expected**: setInterval runs continuously (intentional), no memory leak
- **Evidence Required**: Memory profiler, no unbounded growth

#### 9.4 Dead Code Analysis
**Test Case 9.4.1: All Functions Used**
- **Action**: Review all defined functions
- **Expected**: All functions called:
  - showStep ✓ (called by goToStep, initialization)
  - goToStep ✓ (onclick handlers, prevStep, nextStep)
  - nextStep ✓ (button onclick)
  - prevStep ✓ (button onclick)
  - updateProgress ✓ (showStep)
  - updateNavigationButtons ✓ (showStep)
  - validateStep ✓ (goToStep, nextStep)
  - saveDraftAuto ✓ (interval, manual save, navigation)
  - saveDraftManual ✓ (button onclick, ESC handler)
  - loadDraft ✓ (DOMContentLoaded)
  - clearDraft ✓ (utility function)
  - triggerNINVerify ✓ (button onclick)
  - triggerBVNVerify ✓ (button onclick)
- **Evidence Required**: Call graph analysis

---

### 10. DJANGO INTEGRATION TESTING

#### 10.1 CSRF Protection
**Test Case 10.1.1: AJAX Requests Exempt**
- **Action**: Check API views
- **Expected**: @method_decorator(csrf_exempt, name='dispatch') on:
  - VerifyNINAPIView
  - VerifyBVNAPIView
  - AutoSaveDraftAPIView
- **Evidence Required**: backend/apps/hr/api/kyc_views.py lines 8, 22, 36, 47

#### 10.2 URL Resolution
**Test Case 10.2.1: Wizard URL**
- **Action**: Navigate to http://localhost:8000/hr/admin/onboarding/wizard/
- **Expected**: OnboardingWizardWebView.get() executes, renders template
- **Evidence Required**: 200 response, template loaded

**Test Case 10.2.2: API Endpoints**
- **Action**: POST to /hr/api/v1/kyc/verify-nin/
- **Expected**: VerifyNINAPIView.post() executes, returns JSON
- **Evidence Required**: 200 response, JSON content-type

#### 10.3 Authentication
**Test Case 10.3.1: Unauthenticated Access**
- **Action**: Logout, navigate to wizard URL
- **Expected**: Redirect to login page
- **Evidence Required**: 302 redirect, login URL

**Test Case 10.3.2: Authenticated Access**
- **Action**: Login as HR Admin, navigate to wizard
- **Expected**: Wizard loads successfully
- **Evidence Required**: 200 response, wizard visible

#### 10.4 Template Inheritance
**Test Case 10.4.1: Base Template**
- **Action**: Check template first line
- **Expected**: {% extends "base/_document.html" %}
- **Evidence Required**: Template source line 1

**Test Case 10.4.2: Template Tags**
- **Action**: Check template imports
- **Expected**: {% load hr_permissions %}
- **Evidence Required**: Template source line 2

---

### 11. SECURITY VALIDATION TESTING

#### 11.1 XSS Protection
**Test Case 11.1.1: Input Sanitization**
- **Action**: Enter `<script>alert('XSS')</script>` in firstName
- **Expected**: 
  - Value stored as-is in draft
  - Django template auto-escapes on render
  - No script execution
- **Evidence Required**: Draft data inspection, no alert

**Test Case 11.1.2: DOM Manipulation Safety**
- **Action**: Review innerHTML usage
- **Expected**: Only safe assignments:
  - ind.innerHTML = '⚡ Step 1 Validated...' (static string)
  - nextBtn.innerHTML = 'Next Step &rarr;' (static string)
  - No user input in innerHTML
- **Evidence Required**: Code review

#### 11.2 CSRF (Already Handled)
**Test Case 11.2.1: API Exemption**
- **Action**: Check @csrf_exempt decorator
- **Expected**: Present on all AJAX endpoints (KYC, draft save)
- **Evidence Required**: Decorator confirmed

#### 11.3 Tenant Isolation
**Test Case 11.3.1: Draft Tenant Validation**
- **Action**: Check OnboardingDraft model
- **Expected**: tenant field present, filtered in queries
- **Evidence Required**: Model definition

#### 11.4 Input Validation
**Test Case 11.4.1: NIN Length Validation**
- **Action**: Inspect #ninInput
- **Expected**: maxlength="11" attribute
- **Evidence Required**: DOM attribute

**Test Case 11.4.2: BVN Length Validation**
- **Action**: Inspect #bvnInput
- **Expected**: maxlength="11" attribute
- **Evidence Required**: DOM attribute

---

### 12. PERFORMANCE TESTING

#### 12.1 Page Load Metrics
**Test Case 12.1.1: Initial Load Time**
- **Action**: Measure time to interactive
- **Expected**: < 2 seconds (local dev server)
- **Evidence Required**: Chrome DevTools Performance tab

**Test Case 12.1.2: DOM Size**
- **Action**: Count DOM nodes
- **Expected**: < 1500 nodes (Step 1 only)
- **Evidence Required**: document.querySelectorAll('*').length

#### 12.2 Interaction Performance
**Test Case 12.2.1: Step Transition Time**
- **Action**: Measure showStep() execution
- **Expected**: < 100ms
- **Evidence Required**: console.time/timeEnd

**Test Case 12.2.2: Validation Speed**
- **Action**: Measure validateStep(1) execution
- **Expected**: < 10ms
- **Evidence Required**: Performance benchmark

#### 12.3 AJAX Performance
**Test Case 12.3.1: Auto-Save Latency**
- **Action**: Measure /hr/api/v1/onboarding/draft/auto-save/ response time
- **Expected**: < 500ms (local dev)
- **Evidence Required**: Network tab timing

**Test Case 12.3.2: KYC Verification Latency**
- **Action**: Measure NIN verification response time (sandbox)
- **Expected**: < 1 second (sandbox has no external API)
- **Evidence Required**: Network tab timing

#### 12.4 Memory Usage
**Test Case 12.4.1: Baseline Memory**
- **Action**: Measure heap size after page load
- **Expected**: < 10MB
- **Evidence Required**: Chrome DevTools Memory profiler

**Test Case 12.4.2: After 5 Minutes**
- **Action**: Leave page open, measure heap after 5 minutes (60 auto-saves)
- **Expected**: < 15MB (no unbounded growth)
- **Evidence Required**: Memory profiler comparison

---

### 13. REGRESSION TESTING

#### 13.1 Existing KYC Functionality
**Test Case 13.1.1: NIN Verification Still Works**
- **Action**: Enter NIN, click verify
- **Expected**: Sandbox provider returns mock data, badge updates
- **Evidence Required**: Network success, DOM updates

**Test Case 13.1.2: BVN Verification Still Works**
- **Action**: Enter BVN, click verify
- **Expected**: Sandbox provider returns mock data, badge updates
- **Evidence Required**: Network success, DOM updates

#### 13.2 URL Routing
**Test Case 13.2.1: HR Dashboard Accessible**
- **Action**: Navigate to /hr/dashboard/
- **Expected**: Dashboard loads, no errors
- **Evidence Required**: 200 response

**Test Case 13.2.2: Staff Directory Accessible**
- **Action**: Navigate to /hr/admin/directory/
- **Expected**: Directory loads, wizard link present
- **Evidence Required**: "Add Staff Member (Enterprise Wizard)" link visible

**Test Case 13.2.3: Wizard Link Works**
- **Action**: Click wizard link from directory
- **Expected**: Navigates to /hr/admin/onboarding/wizard/, wizard loads
- **Evidence Required**: URL change, wizard visible

#### 13.3 Template Errors
**Test Case 13.3.1: No Django Template Errors**
- **Action**: Load wizard, check server logs
- **Expected**: No TemplateSyntaxError, no undefined variables
- **Evidence Required**: Clean server console

**Test Case 13.3.2: All Template Tags Resolved**
- **Action**: Check {% url %} tags
- **Expected**: {% url 'hr_admin_directory' %} resolves correctly
- **Evidence Required**: Rendered href="/hr/admin/directory/"

#### 13.4 Sidebar & Navigation
**Test Case 13.4.1: Sidebar Still Works**
- **Action**: Load wizard, check sidebar
- **Expected**: Sidebar loads from base template, HR links present
- **Evidence Required**: Sidebar visible

---

## 📊 Success Criteria Matrix

| Category | Target Score | Pass Threshold |
|----------|--------------|----------------|
| Navigation Functions | 100% | 95% |
| Progress Bar | 100% | 95% |
| Step 1 Validation | 100% | 100% |
| Dojah KYC Integration | 100% | 100% |
| Auto-Save & Drafts | 100% | 95% |
| Keyboard Navigation | 100% | 95% |
| Browser Compatibility | 100% | 95% |
| Dark Mode | 100% | 95% |
| JavaScript Quality | 100% | 100% |
| Django Integration | 100% | 100% |
| Security | 100% | 100% |
| Performance | 100% | 90% |
| Regression Tests | 100% | 100% |

**OVERALL PASS CRITERIA**: ≥ 95% across all categories

---

## 🔧 Defect Classification

### Priority 1 (Blocker)
- JavaScript errors that prevent page load
- Authentication bypass
- Data loss on save
- Complete feature failure

### Priority 2 (Critical)
- Validation not working
- Navigation buttons broken
- Auto-save not persisting
- KYC integration broken

### Priority 3 (Major)
- Keyboard shortcuts not working
- Progress bar not updating
- Memory leaks
- Performance issues

### Priority 4 (Minor)
- UI inconsistencies
- Accessibility improvements
- Non-critical styling

---

## 📝 Test Execution Plan

### Phase 1: Functional Testing (Day 1)
1. Step navigation (1-2 hours)
2. Progress bar (1 hour)
3. Step 1 validation (1 hour)
4. Dojah KYC regression (1 hour)

### Phase 2: Integration Testing (Day 1-2)
1. Auto-save & drafts (2 hours)
2. Keyboard navigation (1 hour)
3. Django integration (1 hour)

### Phase 3: Cross-Browser Testing (Day 2)
1. Chrome testing (1 hour)
2. Firefox testing (1 hour)
3. Edge testing (1 hour)
4. Responsive testing (1 hour)

### Phase 4: Quality & Performance (Day 3)
1. JavaScript quality audit (2 hours)
2. Security validation (2 hours)
3. Performance benchmarks (2 hours)

### Phase 5: Regression & Sign-Off (Day 3)
1. Full regression suite (2 hours)
2. Defect fixes (as needed)
3. Re-test failed cases
4. Final certification

---

## 🎯 Test Deliverables

### 1. PHASE12.4.1_TEST_RESULTS.md
- Test case execution results
- Pass/fail status for each test
- Evidence (screenshots, logs, measurements)
- Defect list with severity

### 2. PHASE12.4.1_BROWSER_VALIDATION.md
- Browser compatibility matrix
- Responsive design validation
- Dark mode verification
- Screenshots per browser

### 3. PHASE12.4.1_SECURITY_REPORT.md
- XSS testing results
- CSRF validation
- Input sanitization audit
- Tenant isolation verification

### 4. PHASE12.4.1_PERFORMANCE_REPORT.md
- Page load metrics
- Interaction performance
- AJAX latency measurements
- Memory profiling results

---

## ✅ Phase Completion Criteria

**READY FOR PHASE 12.4.2 WHEN**:
- [ ] All Priority 1 defects resolved
- [ ] All Priority 2 defects resolved or accepted
- [ ] Overall test pass rate ≥ 95%
- [ ] Zero JavaScript console errors
- [ ] Zero regression failures
- [ ] KYC integration 100% preserved
- [ ] All test deliverables produced
- [ ] Sign-off from QA Lead

**NOT READY UNTIL**:
- Navigation framework is stable
- No memory leaks detected
- Performance meets benchmarks
- Security audit passes

---

## 📌 Notes & Constraints

### DO NOT During This Phase
- ❌ Implement Steps 2-8 (Phase 12.4.2)
- ❌ Implement employee creation (Phase 12.4.3)
- ❌ Redesign the wizard UI
- ❌ Refactor backend services
- ❌ Add new business logic
- ❌ Modify KYC provider code

### DO During This Phase
- ✅ Test all navigation functions
- ✅ Verify auto-save works
- ✅ Validate keyboard shortcuts
- ✅ Measure performance
- ✅ Fix discovered defects
- ✅ Document all findings
- ✅ Produce evidence for every test

### Repository Evidence Requirements
- Every test result must reference specific file paths and line numbers
- Every defect must include before/after code snippets
- Every performance claim must include measurements
- Every browser test must include screenshots
- Every security finding must demonstrate exploit path

---

## 🚀 Next Steps After Phase 12.4.1

Once this phase passes with ≥95%:

**Phase 12.4.2**: Implement Steps 2-8 HTML content
**Phase 12.4.3**: Implement employee creation workflow
**Phase 12.4.4**: End-to-end integration testing
**Phase 12.5**: Production deployment

---

**END OF TEST PLAN**
