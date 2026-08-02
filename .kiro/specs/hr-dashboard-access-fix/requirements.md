# Requirements Document

## Introduction

This specification addresses a critical access control bug where School Admin users (principals, vice principals, and school administrators) are incorrectly redirected to the Employee Self-Service (ESS) portal instead of the HR Admin dashboard when clicking "HR Management" in the sidebar. The root cause is a failure in the middleware to properly resolve HR roles from TenantMembership records for these administrative users.

## Glossary

- **HR_Context_Middleware**: Django middleware component that inspects authenticated users and attaches HR context parameters (hr_employee, hr_role, is_supervisor, hr_permissions) to each request
- **TenantMembership**: Database model linking users to tenants with assigned roles, including fields for user, tenant, role, status, and organizational details
- **HR_Dashboard_View**: Django view that renders the HR Admin dashboard and enforces role-based access control
- **School_Admin_User**: User with administrative roles (school_admin, principal, vice_principal) who should have full HR Admin access
- **HR_Role**: String attribute attached to request object indicating user's primary HR access level (values: 'super_admin', 'hr_admin', 'school_admin', 'hr_officer', 'payroll_admin', 'supervisor', 'employee')
- **Role**: Database model representing a system or tenant-specific role with name, code, description, and associated permissions
- **ESS_Portal**: Employee Self-Service portal at /hr/ess/ for standard employees to view their personal HR data
- **HR_Admin_Dashboard**: Administrative HR dashboard at /hr/admin/dashboard/ for HR staff and administrators to manage all HR functions

## Requirements

### Requirement 1: Role Resolution from TenantMembership

**User Story:** As a School Admin user, I want the system to correctly identify my administrative role from my TenantMembership records, so that I receive appropriate HR access privileges.

#### Acceptance Criteria

1. WHEN HR_Context_Middleware processes a request from an authenticated user, THE HR_Context_Middleware SHALL query TenantMembership records filtered by the user and current tenant
2. WHEN a TenantMembership record exists with a role containing keywords 'school_admin', 'principal', or 'vice_principal' in the role name or code fields, THE HR_Context_Middleware SHALL set request.hr_role to 'school_admin'
3. WHEN a TenantMembership record exists with a role containing keywords 'hr_admin', 'admin', 'manager', or 'director' in the role name or code fields, THE HR_Context_Middleware SHALL set request.hr_role to 'hr_admin'
4. WHEN multiple TenantMembership records exist with different role priorities, THE HR_Context_Middleware SHALL assign the highest priority role (admin roles take precedence over officer and supervisor roles)
5. WHEN no TenantMembership records are found for the user and tenant combination, THE HR_Context_Middleware SHALL set request.hr_role to 'employee' as the default

### Requirement 2: Dashboard Access Control

**User Story:** As a School Admin user, I want to be granted access to the HR Admin dashboard, so that I can manage HR functions for my school.

#### Acceptance Criteria

1. WHEN HR_Dashboard_View receives a request with hr_role set to 'school_admin', THE HR_Dashboard_View SHALL render the HR Admin dashboard template
2. WHEN HR_Dashboard_View receives a request with hr_role set to 'hr_admin', THE HR_Dashboard_View SHALL render the HR Admin dashboard template
3. WHEN HR_Dashboard_View receives a request with hr_role set to 'super_admin', THE HR_Dashboard_View SHALL render the HR Admin dashboard template
4. WHEN HR_Dashboard_View receives a request with hr_role set to 'principal', THE HR_Dashboard_View SHALL render the HR Admin dashboard template
5. WHEN HR_Dashboard_View receives a request with hr_role set to 'vice_principal', THE HR_Dashboard_View SHALL render the HR Admin dashboard template
6. WHEN HR_Dashboard_View receives a request with hr_role set to 'employee', THE HR_Dashboard_View SHALL redirect to the ESS portal at /hr/ess/

### Requirement 3: Fallback Username Pattern Detection

**User Story:** As a system administrator, I want the middleware to detect administrative users by username patterns when TenantMembership records are missing, so that access is not blocked by incomplete data.

#### Acceptance Criteria

1. WHEN HR_Context_Middleware finds zero TenantMembership records for a user, THE HR_Context_Middleware SHALL check the username field for administrative patterns
2. WHEN a username contains 'admin.principal', 'admin.vice', or matches pattern '^principal', THE HR_Context_Middleware SHALL set request.hr_role to 'school_admin'
3. WHEN a username contains 'admin.hr' or 'hr.admin', THE HR_Context_Middleware SHALL set request.hr_role to 'hr_admin'
4. WHEN username pattern detection sets an hr_role, THE HR_Context_Middleware SHALL log a warning message indicating fallback detection was used
5. IF no username pattern matches and no TenantMembership exists, THEN THE HR_Context_Middleware SHALL maintain the default hr_role of 'employee'

### Requirement 4: Middleware Diagnostic Logging

**User Story:** As a developer troubleshooting access issues, I want detailed diagnostic logs from the middleware, so that I can quickly identify the root cause of role resolution failures.

#### Acceptance Criteria

1. WHEN HR_Context_Middleware begins processing a request, THE HR_Context_Middleware SHALL log the username and tenant information
2. WHEN HR_Context_Middleware queries TenantMembership records, THE HR_Context_Middleware SHALL log the count of memberships found
3. WHEN HR_Context_Middleware iterates through TenantMembership roles, THE HR_Context_Middleware SHALL log each role name and code being evaluated
4. WHEN HR_Context_Middleware sets the hr_role attribute, THE HR_Context_Middleware SHALL log the final assigned role value
5. WHEN HR_Context_Middleware uses fallback username pattern detection, THE HR_Context_Middleware SHALL log a warning with the pattern matched and the assigned role

### Requirement 5: Preserve Existing HR Role Hierarchy

**User Story:** As a system architect, I want the fix to preserve the existing HR role hierarchy and access patterns, so that other user types continue to function correctly.

#### Acceptance Criteria

1. WHEN HR_Context_Middleware processes users with 'payroll_admin' roles, THE HR_Context_Middleware SHALL continue to assign hr_role as 'payroll_admin'
2. WHEN HR_Context_Middleware processes users with 'hr_officer' roles, THE HR_Context_Middleware SHALL continue to assign hr_role as 'hr_officer'
3. WHEN HR_Context_Middleware processes users with 'supervisor' roles, THE HR_Context_Middleware SHALL continue to assign hr_role as 'supervisor'
4. WHEN HR_Dashboard_View receives requests with hr_role 'payroll_admin', THE HR_Dashboard_View SHALL redirect to /hr/payroll/
5. WHEN HR_Dashboard_View receives requests with hr_role 'supervisor', THE HR_Dashboard_View SHALL redirect to /hr/manager/team/

### Requirement 6: Multi-Tenancy Integrity

**User Story:** As a platform architect, I want role resolution to respect tenant boundaries, so that users only receive roles applicable to their current tenant context.

#### Acceptance Criteria

1. WHEN HR_Context_Middleware queries TenantMembership records, THE HR_Context_Middleware SHALL filter by both user and the current request tenant
2. WHEN no tenant context exists on the request object, THE HR_Context_Middleware SHALL set hr_role to 'employee' and skip TenantMembership queries
3. WHEN a user has TenantMembership records in multiple tenants, THE HR_Context_Middleware SHALL only consider memberships matching the current request tenant
4. WHEN a user switches between tenant contexts, THE HR_Context_Middleware SHALL re-evaluate roles based on the new tenant's TenantMembership records
5. IF a user has multiple active TenantMembership records for the same tenant, THEN THE HR_Context_Middleware SHALL select the role with highest privilege level

### Requirement 7: Case-Insensitive Role Matching

**User Story:** As a database administrator, I want role matching to be case-insensitive, so that role resolution is not affected by inconsistent capitalization in role names and codes.

#### Acceptance Criteria

1. WHEN HR_Context_Middleware compares role names against keyword lists, THE HR_Context_Middleware SHALL convert role names to lowercase before comparison
2. WHEN HR_Context_Middleware compares role codes against keyword lists, THE HR_Context_Middleware SHALL convert role codes to lowercase before comparison
3. WHEN HR_Context_Middleware performs username pattern matching, THE HR_Context_Middleware SHALL convert usernames to lowercase before comparison
4. THE keyword lists for role matching SHALL contain only lowercase strings
5. THE role resolution logic SHALL produce identical results regardless of the capitalization used in database role name and code fields
