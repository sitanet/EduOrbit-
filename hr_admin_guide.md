# EduOrbit HRMS v1.1.0 — Enterprise HR Administrator Guide (`hr_admin_guide.md`)

> **Target Role**: HR Admin / Director (`hr.admin`)  
> **Access Level**: Full Administrative Control  
> **Module Version**: `v1.1.0-RELEASE`

---

## 1. System Configuration & Tenant Setup

The HR Administrator manages overall SaaS tenant configurations, organization hierarchy, employee number formats, and sub-module feature licensing flags.

### 1.1 Organization Hierarchy Configuration
EduOrbit HRMS supports a **7-Tier Organizational Structure**:
`Company` → `Campus` → `Division` → `Directorate` → `Department` → `Unit` → `Team`

- **Navigation**: Left Sidebar → `Human Resources` → `Organization Hierarchy` (`/hr/admin/org-chart/`).
- **Creating a Position**: Click `+ Add Position` to open the position modal. Specify position title, department name, cost centre, and maximum headcount limit.
- **Position Headcount Metrics**: Tracks Available, Filled, and Vacant seats automatically for recruitment and budgeting.

---

## 2. Staff Directory & Employee Management

### 2.1 Staff Directory Navigation
- **Navigation**: `/hr/admin/directory/`
- **Actions**:
  - `+ Add Staff Member (Enterprise Wizard)`: Launches the 8-Step Enterprise Onboarding Wizard (`/hr/admin/onboarding/wizard/`).
  - `📥 Import Staff`: Opens the CSV bulk staff import wizard (`/hr/import/`).
  - `Search`: Filter staff by name, email, department, or job designation.

### 2.2 Enterprise 8-Step Employee Onboarding Wizard
- **URL**: `/hr/admin/onboarding/wizard/`
- **Steps**:
  1. **Step 1: Personal & Dojah Identity**: Demographics + live NIN & BVN verification with instant photo/metadata display.
  2. **Step 2: Employment & Org Placement**: Employee Number auto-generation (`SCH-{YEAR}-{SEQ:5}`), Campus, Department, Cost Centre, Job Position selection.
  3. **Step 3: Bank & Statutory Setup**: NUBAN bank resolution, PFA, RSA PIN, Tax TIN, PAYE State, NHF, NSITF, ITF, HMO setup.
  4. **Step 4: Compensation & Salary Grade**: Basic, Housing, Transport, Medical, Utility, PAYE, Pension breakdowns.
  5. **Step 5: Emergency & Family**: Next of kin, Emergency contact, Dependants, Blood group, Genotype.
  6. **Step 6: Document Repository**: Upload Passport, Appointment Letter, CV, Certificates with expiry reminders.
  7. **Step 7: System Access & IAM**: User Account creation, Role assignment, 2FA prompt, Welcome Email.
  8. **Step 8: Review & Atomic Activation**: Review summary grid -> Click `Create Employee & Activate` to execute atomic transaction.

---

## 3. Dynamic Approval Workflow Designer

- **Navigation**: `/hr/settings/` → `Workflow Designer`
- **Supported Workflows**: Leave Approval, Attendance Adjustment, Recruitment Hiring, Promotion, Transfer, Salary Increment, Offboarding Exit.
- **Configuration**: Drag-and-drop / node step builder defining approval chains (e.g. *Request → HOD → Dean → Principal → HR → Payroll*).

---

## 4. Security & Audit Logging

- **Audit Trail**: `/hr/audit/` logs every security event, KYC call, salary edit, document upload, and login attempt with timestamp, user IP, and User-Agent.
- **Field-Level Encryption**: NIN, BVN, RSA PIN, and Tax TIN are stored encrypted at rest (AES-256 Fernet). Values are masked (`********1234`) for non-HR admins.
