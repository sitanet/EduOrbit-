# Dashboard Navigation Fix Bugfix Design

## Overview

This bugfix addresses multiple broken dashboard navigation links and a critical database field error in the Django multi-tenant School Management System (EduOrbit/SMS). The bug manifests in three categories:

1. **Database Field Error**: Test code references a removed `subdomain` field on the `Tenant` model, causing `FieldError` exceptions
2. **Missing Dashboard Views**: 22 sidebar navigation links point to incomplete or scaffold implementations lacking proper functionality
3. **Authentication & Tenant Context**: Some views fail to properly handle unauthenticated users or missing tenant context

The fix will ensure all dashboard links work correctly, all views have proper implementations with tenant-aware context, and all references to the removed `subdomain` field are eliminated. The approach is surgical and targeted: fix only what's broken without altering working features like the Control Center, Portal Dashboard, Academic Dashboard, Roles & Permissions, and AI Workspace.

## Glossary

- **Bug_Condition (C)**: The condition that triggers one of the 25 identified bugs - either database field errors, missing view implementations, or authentication/tenant context failures
- **Property (P)**: The desired behavior when bug conditions are met - properly functioning dashboards with correct data, successful test execution, and graceful handling of missing context
- **Preservation**: All existing working dashboard views, authentication flows, and tenant resolution logic that must remain unchanged
- **Tenant**: Organization model representing a corporate group (e.g., Grace Education Group) - the `subdomain` field was removed in migration 0002
- **TenantMiddleware**: Middleware in `backend/apps/core/middleware.py` that resolves tenant via X-Tenant-ID header or CustomDomain lookup
- **View Implementation Pattern**: Django class-based views using `getattr(request, 'tenant', None)` for safe tenant access and `redirect('login_web')` for authentication checks
- **Sidebar Navigation**: Template at `backend/templates/base/_sidebar.html` containing 27 dashboard links organized into Platform, School, Finance, People & Ops, Facilities, and Analytics sections

## Bug Details

### Bug Condition

The bugs manifest across three distinct categories, each with specific trigger conditions:

**Category 1: Database Field Reference Errors**

The bug occurs when test code attempts to create a `Tenant` instance with the removed `subdomain` parameter, causing a `FieldError` during test execution.

**Formal Specification:**
```
FUNCTION isBugCondition_DatabaseField(operation)
  INPUT: operation of type DatabaseOperation
  OUTPUT: boolean
  
  RETURN operation.model == 'Tenant'
         AND 'subdomain' IN operation.parameters
         AND NOT fieldExists('Tenant', 'subdomain')
END FUNCTION
```

**Category 2: Missing Dashboard View Implementations**

The bug occurs when a user clicks a sidebar navigation link that points to a view with incomplete or scaffold implementation, lacking proper dashboard functionality and tenant-aware data.

**Formal Specification:**
```
FUNCTION isBugCondition_MissingView(request)
  INPUT: request of type HttpRequest
  OUTPUT: boolean
  
  DEFINE incomplete_urls = [
    '/tenants/saas-analytics/',
    '/tenants/tenant-dashboard/',
    '/administration/settings/',
    '/admissions/dashboard/',
    '/students/portfolio/',
    '/timetable/builder/',
    '/attendance/dashboard/',
    '/eae/dashboard/',
    '/emrp/dashboard/',
    '/lms/dashboard/',
    '/efbm/dashboard/',
    '/inventory/dashboard/',
    '/hr/dashboard/',
    '/people/directory/',
    '/communication/dashboard/',
    '/workflow/dashboard/',
    '/library/dashboard/',
    '/transport/dashboard/',
    '/hostel/dashboard/',
    '/clinic/dashboard/',
    '/facilities/dashboard/',
    '/analytics/dashboard/'
  ]
  
  RETURN request.path IN incomplete_urls
         AND (viewIsScaffold(request.path) OR viewDataIsIncomplete(request.path))
END FUNCTION
```

**Category 3: Authentication & Tenant Context Failures**

The bug occurs when a view fails to properly handle unauthenticated users or missing tenant context, resulting in crashes, incomplete data display, or missing redirects.

**Formal Specification:**
```
FUNCTION isBugCondition_AuthTenant(request)
  INPUT: request of type HttpRequest
  OUTPUT: boolean
  
  RETURN (NOT request.user.is_authenticated AND NOT isRedirectToLogin(request))
         OR (request.user.is_authenticated AND request.tenant IS NULL AND viewRequiresTenant(request.path))
END FUNCTION
```

### Examples

**Database Field Error:**
- **Input**: `Tenant.objects.create(name="Test School", subdomain="testschool")` in test file
- **Current Behavior**: Raises `FieldError: Cannot resolve keyword 'subdomain' into field`
- **Expected Behavior**: Create tenant successfully without `subdomain` parameter

**Missing Dashboard Views:**
- **Input**: User clicks "SaaS Analytics" link in sidebar
- **Current Behavior**: Displays scaffold template without MRR, ARR, tenant metrics
- **Expected Behavior**: Displays complete SaaS analytics dashboard with MRR ($12,450), active tenants (23), churn rate (2.1%), module adoption charts

- **Input**: User clicks "Attendance" dashboard link
- **Current Behavior**: Shows minimal scaffold page without attendance data
- **Expected Behavior**: Shows attendance dashboard with today's attendance rate (94%), weekly trends chart, recent attendance records

- **Input**: User clicks "Finance & Billing" dashboard link
- **Current Behavior**: Shows empty or scaffold finance page
- **Expected Behavior**: Shows finance dashboard with monthly revenue, pending invoices, recent transactions, payment statistics

**Authentication & Tenant Context:**
- **Input**: Unauthenticated user navigates to `/admissions/dashboard/`
- **Current Behavior**: May display incomplete page or error instead of redirecting to login
- **Expected Behavior**: Redirects to `/login/?next=/admissions/dashboard/` for post-login redirection

- **Input**: Authenticated user with no tenant context accesses `/students/portfolio/`
- **Current Behavior**: May crash or display error when querying tenant-scoped student data
- **Expected Behavior**: Displays empty state message or tenant selection interface instead of crashing

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**

**Existing Working Dashboard Views:**
- Control Center (`/administration/dashboard/`) must continue displaying platform dashboard with schools, subscription plans, and audit logs
- Portal Dashboard (`/portal/dashboard/`) must continue displaying announcements and notifications
- Academic Dashboard (`/academic/dashboard/`) must continue displaying academic years, classes, and subjects
- Roles & Permissions (`/identity/roles/`) must continue displaying role matrix
- AI Workspace (`/ai/workspace/`) must continue displaying AI workspace interface

**Authentication Flow:**
- Successful login must continue redirecting based on user role (superuser → `/administration/dashboard/`, staff → `/tenants/tenant-dashboard/`)
- Logout must continue clearing session and redirecting to login page
- Login page must continue accepting credentials and establishing authenticated sessions

**Tenant Resolution (TenantMiddleware):**
- Resolving tenant from X-Tenant-ID header must continue working for mobile/REST clients
- Resolving tenant from CustomDomain lookup must continue working for custom domain requests
- Setting `request.tenant` to None when tenant cannot be resolved must continue allowing views to handle missing tenant gracefully
- Local development fallback to first active tenant must continue working

**View Query Patterns:**
- Views using `getattr(request, 'tenant', None)` for safe tenant access must continue working
- Views using `.filter(tenant=tenant)` for tenant-scoped queries must continue working
- Template rendering with `base/_document.html` and `base/_sidebar.html` must continue working

**Authorization Checks:**
- Superuser-only views must continue redirecting non-superusers to appropriate dashboards or showing access denied
- Staff-only views must continue enforcing staff status checks

**Scope:**
All inputs that do NOT involve the 25 identified bug conditions should be completely unaffected by this fix. This includes:
- All working dashboard views and their existing functionality
- All existing authentication and authorization logic
- All existing tenant resolution mechanisms
- All existing template rendering patterns
- All existing database models except removing `subdomain` references from tests

## Hypothesized Root Cause

Based on the bug requirements analysis, the most likely root causes are:

### 1. **Incomplete Migration Cleanup**
The `subdomain` field was removed from the `Tenant` model in migration `0002_subscriptionplan_alter_tenant_options_and_more.py`, but test code in `backend/apps/core/tests/test_models.py` still references this field when creating test tenant instances. This causes `FieldError` exceptions during test execution.

**Evidence**: The requirements document explicitly states the field was removed in migration 0002, but test code still uses `subdomain="testschool"` parameter.

### 2. **Scaffold Views Without Implementation**
Many dashboard URLs are defined in `urls.py` files but point to views that are either:
- Minimal scaffold implementations returning empty templates
- Missing proper data queries for tenant-scoped content
- Lacking dashboard-specific metrics and statistics

**Evidence**: The requirements document identifies 22 dashboard URLs that display scaffold templates or incomplete data. The existing `PlatformDashboardWebView` and `PortalDashboardWebView` show the proper pattern (authentication check, tenant-aware queries, context population), but other apps lack similar implementations.

### 3. **Inconsistent Authentication Checks**
Some views lack the standard authentication check pattern seen in working views:
```python
if not request.user.is_authenticated:
    return redirect('login_web')
```

**Evidence**: Requirements document states "some views may fail to properly redirect to the login page" for unauthenticated users.

### 4. **Missing Tenant Context Error Handling**
Some views may not handle the case where `request.tenant` is `None`, either:
- Attempting to query with `tenant=None` which returns no results but doesn't crash
- Not providing user-friendly empty state messaging when tenant context is missing

**Evidence**: Requirements document states "the system may crash or display incomplete data instead of gracefully handling the missing tenant."

### 5. **Missing URL Route Definitions**
Some sidebar links may point to URL routes that don't exist or aren't properly registered in the app's `urls.py` file, though this is less likely given the requirements focus on "incomplete implementations" rather than 404 errors.

## Correctness Properties

Property 1: Bug Condition - Database Field References Eliminated

_For any_ test code that creates `Tenant` model instances, the fixed code SHALL NOT reference the removed `subdomain` field and SHALL successfully create tenant instances without `FieldError` exceptions.

**Validates: Requirements 2.1**

Property 2: Bug Condition - Functional Dashboard Views Implemented

_For any_ user clicking on one of the 22 identified incomplete dashboard navigation links, the fixed view SHALL display a complete functional dashboard with:
- Proper authentication checks redirecting unauthenticated users to login
- Tenant-aware data queries using `getattr(request, 'tenant', None)`
- Dashboard-specific metrics, statistics, and content appropriate to the module
- Proper template rendering with the existing base template structure

**Validates: Requirements 2.2 through 2.23**

Property 3: Bug Condition - Graceful Authentication & Tenant Context Handling

_For any_ dashboard view accessed by unauthenticated users or users without tenant context, the fixed view SHALL:
- Redirect unauthenticated users to `/login/` with appropriate `next` parameter
- Handle missing tenant context gracefully by displaying empty state messaging or tenant selection interface instead of crashing

**Validates: Requirements 2.24, 2.25**

Property 4: Preservation - Existing Working Dashboard Views

_For any_ user accessing the five working dashboard views (Control Center, Portal Dashboard, Academic Dashboard, Roles & Permissions, AI Workspace), the fixed code SHALL produce exactly the same behavior as the original code, preserving all existing functionality including data queries, template rendering, and user experience.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

Property 5: Preservation - Authentication & Authorization Flows

_For any_ user login, logout, or authorization check operation, the fixed code SHALL produce exactly the same behavior as the original code, preserving role-based dashboard redirection, session management, and access control enforcement.

**Validates: Requirements 3.6, 3.7, 3.13**

Property 6: Preservation - Tenant Resolution Logic

_For any_ HTTP request processed by TenantMiddleware, the fixed code SHALL produce exactly the same tenant resolution behavior as the original code, preserving X-Tenant-ID header resolution, CustomDomain lookup, local development fallback, and setting `request.tenant` to None when resolution fails.

**Validates: Requirements 3.8, 3.9, 3.10, 3.11, 3.12**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct, the following changes are required:

#### **File 1**: `backend/apps/core/tests/test_models.py`

**Function**: `BaseModelTests.setUp()`

**Specific Changes**:
1. **Remove subdomain parameter**: Change `Tenant.objects.create(name="Test School", subdomain="testschool")` to `Tenant.objects.create(name="Test School")`
2. **Remove assertion checks**: Remove any test assertions that validate the `subdomain` field value

#### **File 2**: `backend/apps/tenants/views_web.py`

**Function**: New view class `SaaSAnalyticsWebView`

**Specific Changes**:
1. **Create new view**: Implement view class for `/tenants/saas-analytics/` route
2. **Add authentication check**: Use standard `if not request.user.is_authenticated: return redirect('login_web')` pattern
3. **Add superuser check**: Restrict access to superusers only
4. **Query platform metrics**: Calculate MRR, ARR, active tenant count, churn rate, module adoption statistics
5. **Render template**: Return `render(request, 'tenants/saas_analytics.html', context)`

#### **File 3**: `backend/apps/tenants/views_web.py`

**Function**: Enhance existing `TenantDashboardWebView`

**Specific Changes**:
1. **Add comprehensive queries**: Query schools, subscriptions, campuses, and recent activity for tenant
2. **Add statistics**: Calculate school count, active users, subscription status
3. **Enhance context**: Pass comprehensive tenant dashboard data to template

#### **File 4**: `backend/apps/administration/views_web.py`

**Function**: Enhance existing `SchoolSettingsWebView`

**Specific Changes**:
1. **Add comprehensive queries**: Query subscription plans, billing configurations, active modules
2. **Add platform configuration**: Include platform settings and feature flags
3. **Enhance context**: Pass complete platform settings data to template

#### **File 5-25**: Dashboard View Implementations for Remaining Apps

For each of the following apps, create or enhance dashboard view classes:
- `backend/apps/admissions/views_web.py` - `AdmissionsDashboardWebView`
- `backend/apps/students/views_web.py` - `StudentPortfolioWebView`
- `backend/apps/timetable/views_web.py` - `TimetableBuilderWebView`
- `backend/apps/attendance/views_web.py` - `AttendanceDashboardWebView`
- `backend/apps/eae/views_web.py` - `ExamsDashboardWebView`
- `backend/apps/emrp/views_web.py` - `ReportsDashboardWebView`
- `backend/apps/lms/views_web.py` - `LMSDashboardWebView`
- `backend/apps/efbm/views_web.py` - `FinanceDashboardWebView`
- `backend/apps/inventory/views_web.py` - `InventoryDashboardWebView`
- `backend/apps/hr/views_web.py` - `HRDashboardWebView`
- `backend/apps/people/views_web.py` - `PeopleDirectoryWebView`
- `backend/apps/communication/views_web.py` - `CommunicationDashboardWebView`
- `backend/apps/workflow/views_web.py` - `WorkflowDashboardWebView`
- `backend/apps/library/views_web.py` - `LibraryDashboardWebView`
- `backend/apps/transport/views_web.py` - `TransportDashboardWebView`
- `backend/apps/hostel/views_web.py` - `HostelDashboardWebView`
- `backend/apps/clinic/views_web.py` - `ClinicDashboardWebView`
- `backend/apps/facilities/views_web.py` - `FacilitiesDashboardWebView`
- `backend/apps/analytics/views_web.py` - `AnalyticsDashboardWebView`

**Standard Pattern for Each View**:
```python
class [Module]DashboardWebView(View):
    def get(self, request):
        # 1. Authentication check
        if not request.user.is_authenticated:
            return redirect('login_web')
        
        # 2. Tenant resolution with graceful handling
        tenant = getattr(request, 'tenant', None)
        
        # 3. Module-specific data queries (tenant-scoped where applicable)
        # Query relevant models for dashboard metrics
        
        # 4. Statistics calculation
        # Calculate counts, percentages, trends
        
        # 5. Context population
        context = {
            'tenant': tenant,
            # ... module-specific data
        }
        
        # 6. Template rendering
        return render(request, '[app]/dashboard.html', context)
```

#### **URL Registration**

Ensure each new view is properly registered in the respective app's `urls.py` file with appropriate URL pattern and view name.

## Testing Strategy

### Validation Approach

The testing strategy follows a three-phase approach:

1. **Exploratory Bug Condition Checking**: Run tests on UNFIXED code to surface counterexamples and confirm root cause hypotheses
2. **Fix Checking**: Verify that for all inputs where bug conditions hold, the fixed code produces expected behavior
3. **Preservation Checking**: Verify that for all inputs where bug conditions do NOT hold, the fixed code produces the same results as the original code

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bugs BEFORE implementing the fix. Confirm or refute the root cause analysis. If we refute, we will need to re-hypothesize.

#### Test Plan 1: Database Field Error

**Approach**: Run existing test suite to observe `FieldError` on UNFIXED code.

**Test Cases**:
1. **Test Execution**: Run `python manage.py test backend.apps.core.tests.test_models` (will fail on unfixed code)
2. **Error Pattern**: Observe `FieldError: Cannot resolve keyword 'subdomain' into field` exception
3. **Root Cause Confirmation**: Verify error occurs in `setUp()` method at line creating tenant with `subdomain="testschool"`

**Expected Counterexamples**:
- Test suite fails with `FieldError` when attempting to create `Tenant` with `subdomain` parameter
- Confirms root cause: migration removed field but test code still references it

#### Test Plan 2: Missing Dashboard Views

**Approach**: Manually navigate to each of the 22 dashboard URLs and observe incomplete implementations on UNFIXED code.

**Test Cases**:
1. **SaaS Analytics Test**: Navigate to `/tenants/saas-analytics/` as superuser (will show scaffold on unfixed code)
   - Observe: Empty or minimal template without MRR, ARR, tenant metrics
   
2. **Admissions Dashboard Test**: Navigate to `/admissions/dashboard/` as authenticated user (will show scaffold on unfixed code)
   - Observe: Empty or minimal template without admissions statistics
   
3. **Attendance Dashboard Test**: Navigate to `/attendance/dashboard/` as authenticated user (will show scaffold on unfixed code)
   - Observe: Empty or minimal template without attendance data

4. **Finance Dashboard Test**: Navigate to `/efbm/dashboard/` as authenticated user (will show scaffold on unfixed code)
   - Observe: Empty or minimal template without billing statistics

5. **Repeat for all 22 dashboard URLs**: Document incomplete implementations, missing data queries, missing metrics

**Expected Counterexamples**:
- Dashboard views render templates without proper data context
- Views lack tenant-aware queries for module-specific data
- Templates display empty states or placeholder content instead of functional dashboards
- Confirms root cause: views are scaffold implementations without proper functionality

#### Test Plan 3: Authentication & Tenant Context

**Approach**: Test unauthenticated access and missing tenant context scenarios on UNFIXED code.

**Test Cases**:
1. **Unauthenticated Access Test**: Log out and navigate directly to `/admissions/dashboard/` (may fail on unfixed code)
   - Observe: Whether view redirects to login or displays incomplete page/error
   
2. **Missing Tenant Context Test**: Modify middleware temporarily to set `request.tenant = None` and access `/students/portfolio/` (may fail on unfixed code)
   - Observe: Whether view crashes or handles missing tenant gracefully

**Expected Counterexamples**:
- Some views fail to redirect unauthenticated users to login page
- Some views crash or display errors when `request.tenant` is None
- Confirms root cause: inconsistent authentication checks and missing tenant context error handling

### Fix Checking

**Goal**: Verify that for all inputs where bug conditions hold, the fixed code produces the expected behavior.

#### Category 1: Database Field Fix Checking

**Pseudocode:**
```
FOR ALL test_operation WHERE isBugCondition_DatabaseField(test_operation) DO
  result := execute_test_with_fixed_code(test_operation)
  ASSERT result.status == "PASS"
  ASSERT NOT contains(result.errors, "FieldError")
  ASSERT tenant_created_successfully(result)
END FOR
```

**Test Plan**:
- Run `python manage.py test backend.apps.core.tests.test_models` on FIXED code
- Verify all tests pass without `FieldError` exceptions
- Verify tenant instances are created successfully

#### Category 2: Dashboard View Fix Checking

**Pseudocode:**
```
FOR ALL dashboard_url WHERE isBugCondition_MissingView(dashboard_url) DO
  response := GET_authenticated(dashboard_url)
  ASSERT response.status_code == 200
  ASSERT has_proper_authentication_check(dashboard_url)
  ASSERT has_tenant_aware_queries(dashboard_url)
  ASSERT has_dashboard_metrics(response.context)
  ASSERT template_renders_successfully(response)
END FOR
```

**Test Plan**:
1. **Authentication Check Verification**:
   - For each of 22 dashboard URLs, verify unauthenticated GET redirects to `/login/`
   - Verify authenticated GET with valid tenant returns 200 OK

2. **Data Context Verification**:
   - For each dashboard, verify response context includes tenant and module-specific data
   - Verify queries are tenant-scoped where applicable
   - Verify dashboard metrics are calculated correctly

3. **Template Rendering Verification**:
   - Verify each dashboard renders proper template (not scaffold)
   - Verify templates display data from context
   - Verify no template rendering errors

#### Category 3: Auth & Tenant Context Fix Checking

**Pseudocode:**
```
FOR ALL request WHERE isBugCondition_AuthTenant(request) DO
  IF NOT request.user.is_authenticated THEN
    response := dashboard_view(request)
    ASSERT response.status_code == 302  // Redirect
    ASSERT response.url STARTS_WITH "/login/"
  END IF
  
  IF request.tenant IS NULL THEN
    response := dashboard_view(request)
    ASSERT response.status_code == 200
    ASSERT has_empty_state_handling(response)
    ASSERT NOT response.raises_exception
  END IF
END FOR
```

**Test Plan**:
- Test unauthenticated access to all 22 dashboard URLs - verify redirect to login
- Test authenticated access with `request.tenant = None` - verify graceful handling (no crashes)
- Verify empty state messaging appears when tenant context is missing

### Preservation Checking

**Goal**: Verify that for all inputs where bug conditions do NOT hold, the fixed code produces the same results as the original code.

#### Preservation Category 1: Existing Working Dashboards

**Pseudocode:**
```
DEFINE working_dashboards = [
  '/administration/dashboard/',
  '/portal/dashboard/',
  '/academic/dashboard/',
  '/identity/roles/',
  '/ai/workspace/'
]

FOR ALL url IN working_dashboards DO
  original_response := GET_original(url, authenticated_request)
  fixed_response := GET_fixed(url, authenticated_request)
  
  ASSERT original_response.status_code == fixed_response.status_code
  ASSERT original_response.context == fixed_response.context
  ASSERT original_response.template_name == fixed_response.template_name
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many test cases automatically across different user roles and tenant configurations
- It catches edge cases that manual tests might miss (different user types, various tenant states)
- It provides strong guarantees that existing behavior is unchanged

**Test Plan**:
1. **Observe behavior on UNFIXED code first**: For each of the 5 working dashboards, document:
   - Exact response status codes
   - Context data structure and values
   - Template rendering output
   - Authentication flow behavior

2. **Write property-based tests**: Create tests that:
   - Generate various authenticated user scenarios (superuser, staff, regular user)
   - Generate various tenant contexts (active tenant, multiple schools, no schools)
   - Verify all 5 working dashboards produce identical responses before and after fix

3. **Run preservation tests**: Execute tests against both UNFIXED and FIXED code to verify identical behavior

**Test Cases**:
1. **Control Center Preservation**: Verify `/administration/dashboard/` continues displaying schools, plans, and audits identically
2. **Portal Dashboard Preservation**: Verify `/portal/dashboard/` continues displaying announcements and notifications identically
3. **Academic Dashboard Preservation**: Verify `/academic/dashboard/` continues displaying academic data identically
4. **Roles & Permissions Preservation**: Verify `/identity/roles/` continues displaying role matrix identically
5. **AI Workspace Preservation**: Verify `/ai/workspace/` continues displaying AI interface identically

#### Preservation Category 2: Authentication & Tenant Resolution

**Pseudocode:**
```
FOR ALL request WHERE NOT isBugCondition_AuthTenant(request) DO
  // Test authentication flow preservation
  login_response_original := login_original(credentials)
  login_response_fixed := login_fixed(credentials)
  ASSERT login_response_original.redirect_url == login_response_fixed.redirect_url
  
  // Test tenant resolution preservation
  tenant_original := resolve_tenant_original(request)
  tenant_fixed := resolve_tenant_fixed(request)
  ASSERT tenant_original == tenant_fixed
END FOR
```

**Test Plan**:
1. **Authentication Flow Preservation**: Observe login/logout behavior on UNFIXED code, then verify identical behavior on FIXED code:
   - Superuser login redirects to `/administration/dashboard/`
   - Staff login redirects to appropriate dashboard
   - Logout clears session and redirects to login

2. **Tenant Resolution Preservation**: Test middleware behavior:
   - X-Tenant-ID header resolution works identically
   - CustomDomain lookup works identically
   - Local development fallback works identically
   - Setting `request.tenant = None` when resolution fails works identically

3. **Authorization Preservation**: Test access control:
   - Superuser-only views continue blocking non-superusers
   - Staff-only views continue enforcing staff checks

### Unit Tests

#### Database Field Tests
- Test creating `Tenant` without `subdomain` field succeeds
- Test querying `Tenant` model doesn't reference `subdomain` field
- Test all tenant-related tests in `backend/apps/core/tests/test_models.py` pass

#### Dashboard View Tests (for each of 22 fixed views)
- Test unauthenticated access redirects to `/login/` with proper `next` parameter
- Test authenticated access with valid tenant returns 200 OK
- Test response context includes expected dashboard data
- Test tenant-scoped queries filter correctly by tenant
- Test dashboard metrics are calculated correctly
- Test missing tenant context is handled gracefully (no crashes)

#### Authentication & Authorization Tests
- Test login redirects to correct dashboard based on user role
- Test logout clears session and redirects to login
- Test superuser-only views block non-superusers
- Test staff-only views block non-staff users

### Property-Based Tests

#### Tenant Context Property Tests
- Generate random tenant configurations (with/without schools, with/without subscriptions)
- For all generated scenarios, verify dashboard views handle tenant context correctly
- For all generated scenarios, verify views don't crash on missing tenant

#### Authentication Property Tests
- Generate random user types (authenticated/unauthenticated, superuser/staff/regular)
- For all generated scenarios, verify authentication checks behave correctly
- For all generated scenarios, verify redirects work as expected

#### Dashboard Data Property Tests
- Generate random module data configurations (empty, sparse, full)
- For all generated scenarios, verify dashboards display appropriate data
- For all generated scenarios, verify empty states are handled properly

#### Preservation Property Tests
- Generate random request scenarios for working dashboards
- For all generated scenarios, verify fixed code produces identical responses to original code
- For all generated scenarios, verify tenant resolution logic remains unchanged

### Integration Tests

#### Full Navigation Flow Tests
- Test logging in as superuser and navigating through all Platform section links
- Test logging in as staff and navigating through all School section links
- Test navigating through Finance, People & Ops, Facilities, and Analytics sections
- Verify all 27 sidebar links work correctly after fix

#### Tenant Context Switching Tests
- Test navigating dashboards while switching between different tenant contexts
- Test handling of missing tenant context across multiple dashboard views
- Verify tenant-scoped data isolation works correctly

#### Authentication Flow Integration Tests
- Test full login → dashboard navigation → logout flow
- Test unauthenticated access attempts → redirect to login → post-login redirect back
- Test role-based dashboard access patterns across user types
