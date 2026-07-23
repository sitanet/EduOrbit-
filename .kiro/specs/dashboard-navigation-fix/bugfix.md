# Bugfix Requirements Document

## Introduction

The superuser dashboard navigation in the Django multi-tenant School Management System (EduOrbit/SMS) has multiple broken links and incomplete implementations. The sidebar at `/administration/dashboard/` contains 27 menu items, many of which either:
- Reference views that don't exist or have minimal scaffold implementations
- Navigate to routes with incomplete templates
- Produce errors when accessed

Additionally, there is a critical database field error: the `subdomain` field was removed from the `Tenant` model in migration `0002_subscriptionplan_alter_tenant_options_and_more.py`, but test code still references this removed field, causing `FieldError: Cannot resolve keyword 'subdomain' into field` errors.

This bugfix ensures all sidebar navigation links work correctly, all dashboard views have proper implementations with tenant context, and all references to the removed `subdomain` field are eliminated.

## Bug Analysis

### Current Behavior (Defect)

#### 1. Database Field References

1.1 WHEN test code in `backend/apps/core/tests/test_models.py` attempts to create a Tenant with `subdomain="testschool"` THEN the system raises `FieldError: Cannot resolve keyword 'subdomain' into field` because the subdomain field was removed in migration 0002

#### 2. Missing or Incomplete Dashboard Views

1.2 WHEN a user clicks on the "SaaS Analytics" link (`/tenants/saas-analytics/`) in the sidebar THEN the system may display a scaffold template without proper functionality

1.3 WHEN a user clicks on the "Tenant Schools" link (`/tenants/tenant-dashboard/`) in the sidebar THEN the system may display incomplete tenant information or fail to load

1.4 WHEN a user clicks on the "Platform Settings" link (`/administration/settings/`) in the sidebar THEN the system may display a minimal settings page without proper configuration options

1.5 WHEN a user clicks on "Admissions" (`/admissions/dashboard/`) THEN the system may display a scaffold dashboard without admissions-specific content

1.6 WHEN a user clicks on "Students" (`/students/portfolio/`) THEN the system may display a minimal student list without proper portfolio functionality

1.7 WHEN a user clicks on "Timetable" (`/timetable/builder/`) THEN the system may display a scaffold timetable builder without proper functionality

1.8 WHEN a user clicks on "Attendance" (`/attendance/dashboard/`) THEN the system may display a scaffold attendance dashboard without proper attendance tracking features

1.9 WHEN a user clicks on "Exams & Grades" (`/eae/dashboard/`) THEN the system may display a scaffold dashboard without exam and grading functionality

1.10 WHEN a user clicks on "Reports & CBT" (`/emrp/dashboard/`) THEN the system may display a scaffold dashboard without reporting or CBT features

1.11 WHEN a user clicks on "E-Learning" (`/lms/dashboard/`) THEN the system may display a scaffold LMS dashboard without learning management features

1.12 WHEN a user clicks on "Finance & Billing" (`/efbm/dashboard/`) THEN the system may display a scaffold finance dashboard without proper billing features

1.13 WHEN a user clicks on "Inventory" (`/inventory/dashboard/`) THEN the system may display a scaffold inventory dashboard without inventory management features

1.14 WHEN a user clicks on "Human Resources" (`/hr/dashboard/`) THEN the system may display a scaffold HR dashboard without HR management features

1.15 WHEN a user clicks on "People Directory" (`/people/directory/`) THEN the system may display a minimal directory without comprehensive people information

1.16 WHEN a user clicks on "Communication" (`/communication/dashboard/`) THEN the system may display a scaffold communication dashboard without messaging features

1.17 WHEN a user clicks on "Workflow & Approvals" (`/workflow/dashboard/`) THEN the system may display a scaffold workflow dashboard without approval management features

1.18 WHEN a user clicks on "Library" (`/library/dashboard/`) THEN the system may display a scaffold library dashboard without library management features

1.19 WHEN a user clicks on "Transport" (`/transport/dashboard/`) THEN the system may display a scaffold transport dashboard without transport management features

1.20 WHEN a user clicks on "Hostel" (`/hostel/dashboard/`) THEN the system may display a scaffold hostel dashboard without hostel management features

1.21 WHEN a user clicks on "Clinic" (`/clinic/dashboard/`) THEN the system may display a scaffold clinic dashboard without health management features

1.22 WHEN a user clicks on "Facilities" (`/facilities/dashboard/`) THEN the system may display a scaffold facilities dashboard without facility management features

1.23 WHEN a user clicks on "Analytics" (`/analytics/dashboard/`) THEN the system may display a scaffold analytics dashboard without proper analytics features

#### 3. Missing Authentication and Tenant Context

1.24 WHEN an unauthenticated user attempts to access any dashboard URL THEN some views may fail to properly redirect to the login page

1.25 WHEN an authenticated user without tenant context accesses a tenant-specific dashboard THEN the system may crash or display incomplete data instead of gracefully handling the missing tenant

### Expected Behavior (Correct)

#### 1. Database Field References

2.1 WHEN test code in `backend/apps/core/tests/test_models.py` creates a Tenant for testing THEN the system SHALL create the tenant without referencing the removed `subdomain` field

#### 2. Functional Dashboard Views

2.2 WHEN a user clicks on "SaaS Analytics" (`/tenants/saas-analytics/`) THEN the system SHALL display a complete SaaS analytics dashboard with MRR, ARR, tenant counts, and module adoption metrics

2.3 WHEN a user clicks on "Tenant Schools" (`/tenants/tenant-dashboard/`) THEN the system SHALL display a complete tenant dashboard showing all schools, subscriptions, and tenant information

2.4 WHEN a user clicks on "Platform Settings" (`/administration/settings/`) THEN the system SHALL display a complete platform settings page with subscription and configuration options

2.5 WHEN a user clicks on "Admissions" (`/admissions/dashboard/`) THEN the system SHALL display a functional admissions dashboard with application statistics and recent admissions data

2.6 WHEN a user clicks on "Students" (`/students/portfolio/`) THEN the system SHALL display a functional student portfolio page with student list and basic statistics

2.7 WHEN a user clicks on "Timetable" (`/timetable/builder/`) THEN the system SHALL display a functional timetable builder with existing timetable data or a setup interface

2.8 WHEN a user clicks on "Attendance" (`/attendance/dashboard/`) THEN the system SHALL display a functional attendance dashboard with attendance statistics and recent records

2.9 WHEN a user clicks on "Exams & Grades" (`/eae/dashboard/`) THEN the system SHALL display a functional exam dashboard with exam schedules and grading statistics

2.10 WHEN a user clicks on "Reports & CBT" (`/emrp/dashboard/`) THEN the system SHALL display a functional reporting dashboard with report templates and CBT test statistics

2.11 WHEN a user clicks on "E-Learning" (`/lms/dashboard/`) THEN the system SHALL display a functional LMS dashboard with course statistics and recent learning activity

2.12 WHEN a user clicks on "Finance & Billing" (`/efbm/dashboard/`) THEN the system SHALL display a functional finance dashboard with billing statistics and recent transactions

2.13 WHEN a user clicks on "Inventory" (`/inventory/dashboard/`) THEN the system SHALL display a functional inventory dashboard with stock levels and recent inventory movements

2.14 WHEN a user clicks on "Human Resources" (`/hr/dashboard/`) THEN the system SHALL display a functional HR dashboard with employee statistics and recent HR activities

2.15 WHEN a user clicks on "People Directory" (`/people/directory/`) THEN the system SHALL display a functional people directory with comprehensive staff and student information

2.16 WHEN a user clicks on "Communication" (`/communication/dashboard/`) THEN the system SHALL display a functional communication dashboard with message statistics and recent communications

2.17 WHEN a user clicks on "Workflow & Approvals" (`/workflow/dashboard/`) THEN the system SHALL display a functional workflow dashboard with pending approvals and workflow statistics

2.18 WHEN a user clicks on "Library" (`/library/dashboard/`) THEN the system SHALL display a functional library dashboard with book statistics and recent borrowing activity

2.19 WHEN a user clicks on "Transport" (`/transport/dashboard/`) THEN the system SHALL display a functional transport dashboard with vehicle information and route statistics

2.20 WHEN a user clicks on "Hostel" (`/hostel/dashboard/`) THEN the system SHALL display a functional hostel dashboard with occupancy statistics and resident information

2.21 WHEN a user clicks on "Clinic" (`/clinic/dashboard/`) THEN the system SHALL display a functional clinic dashboard with health visit statistics and recent medical records

2.22 WHEN a user clicks on "Facilities" (`/facilities/dashboard/`) THEN the system SHALL display a functional facilities dashboard with facility usage statistics and maintenance records

2.23 WHEN a user clicks on "Analytics" (`/analytics/dashboard/`) THEN the system SHALL display a functional analytics dashboard with executive-level insights and data visualizations

#### 3. Proper Authentication and Tenant Context

2.24 WHEN an unauthenticated user attempts to access any dashboard URL THEN the system SHALL redirect to the login page with a next parameter for post-login redirection

2.25 WHEN an authenticated user without tenant context accesses a tenant-specific dashboard THEN the system SHALL either display a tenant selection interface or show empty state messaging instead of crashing

### Unchanged Behavior (Regression Prevention)

#### 1. Existing Working Features

3.1 WHEN a superuser accesses `/administration/dashboard/` (Control Center) THEN the system SHALL CONTINUE TO display the platform dashboard with schools, plans, and audits

3.2 WHEN a user accesses `/portal/dashboard/` (My Dashboard) THEN the system SHALL CONTINUE TO display the portal dashboard with announcements and notifications

3.3 WHEN a user accesses `/academic/dashboard/` (Academics) THEN the system SHALL CONTINUE TO display the academic dashboard with years, classes, and subjects

3.4 WHEN a user accesses `/identity/roles/` (Roles & Permissions) THEN the system SHALL CONTINUE TO display the role matrix with roles and permissions

3.5 WHEN a user accesses `/ai/workspace/` (AI Workspace) THEN the system SHALL CONTINUE TO display the AI workspace interface

#### 2. Authentication Flow

3.6 WHEN a user logs in successfully THEN the system SHALL CONTINUE TO redirect to the appropriate dashboard based on user role (superuser → /administration/dashboard/, staff → /tenants/tenant-dashboard/, etc.)

3.7 WHEN a user logs out THEN the system SHALL CONTINUE TO clear the session and redirect to the login page

#### 3. Tenant Resolution

3.8 WHEN TenantMiddleware receives a request with X-Tenant-ID header THEN the system SHALL CONTINUE TO resolve the tenant from the header value

3.9 WHEN TenantMiddleware receives a request with a custom domain THEN the system SHALL CONTINUE TO resolve the tenant from the CustomDomain model

3.10 WHEN TenantMiddleware cannot resolve a tenant THEN the system SHALL CONTINUE TO set request.tenant to None and allow the view to handle the missing tenant gracefully

#### 4. Existing View Functionality

3.11 WHEN views query models filtered by tenant THEN the system SHALL CONTINUE TO use `getattr(request, 'tenant', None)` for safe tenant access

3.12 WHEN views render templates THEN the system SHALL CONTINUE TO use the existing template structure with base/_document.html and base/_sidebar.html

3.13 WHEN superuser-only views are accessed by non-superusers THEN the system SHALL CONTINUE TO redirect to an appropriate dashboard or show access denied
