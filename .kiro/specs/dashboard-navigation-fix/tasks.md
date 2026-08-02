# Implementation Plan

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - Database Field Error on Tenant Creation
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the bug exists
  - **Scoped PBT Approach**: Target the exact failing test case from `backend/apps/core/tests/test_models.py`
  - Test that creating a Tenant with `subdomain="testschool"` raises `FieldError: Cannot resolve keyword 'subdomain' into field`
  - Run test: `python manage.py test backend.apps.core.tests.test_models`
  - **EXPECTED OUTCOME**: Test FAILS with `FieldError` (this is correct - it proves the bug exists)
  - Document the exact error: "FieldError occurs in test_models.py at line X when attempting to create Tenant with removed subdomain field"
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.1, 2.1_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Existing Dashboard and Tenant Functionality
  - **IMPORTANT**: Follow observation-first methodology
  - Observe: Navigate to Control Center (`/administration/dashboard/`) as superuser on unfixed code - record behavior
  - Observe: Navigate to Portal Dashboard (`/portal/dashboard/`) as authenticated user on unfixed code - record behavior
  - Observe: Navigate to Academic Dashboard (`/academic/dashboard/`) as authenticated user on unfixed code - record behavior
  - Observe: Test tenant resolution via X-Tenant-ID header on unfixed code - record behavior
  - Observe: Test authentication redirect flow (login → appropriate dashboard) on unfixed code - record behavior
  - Write property-based tests capturing observed behavior patterns for working dashboards
  - Write property-based tests capturing tenant resolution and authentication flows
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10, 3.11, 3.12, 3.13_

- [x] 3. Fix for database field references and incomplete dashboard implementations

  - [x] 3.1 Remove subdomain field references from test code
    - Open file `backend/apps/core/tests/test_models.py`
    - Find line creating Tenant with `subdomain="testschool"` parameter
    - Remove the `subdomain` parameter from Tenant.objects.create() call
    - Save file
    - _Bug_Condition: isBugCondition_DatabaseField(operation) where operation references removed subdomain field_
    - _Expected_Behavior: Tenant.objects.create() succeeds without FieldError_
    - _Preservation: All other test cases continue passing_
    - _Requirements: 1.1, 2.1_

  - [x] 3.2 Enhance Tenant Dashboard view with Service layer (Architecture Compliance)
    - File: `backend/apps/tenants/views_web.py` - `TenantDashboardWebView`
    - **Architecture Violation**: Current implementation has direct ORM queries in view (violates Clean Architecture - views must be thin)
