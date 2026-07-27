# EduOrbit ERP v3.0.0 — Interactive Web Credentials & Demo Accounts Directory

> **Portal Status**: `ACTIVE & ACCESSIBLE`  
> **Web Portal Route**: `/demo-credentials/` or `/identity/demo-portal/`  
> **Default Password for All Roles**: `EduOrbit@2026`  
> **Release Tag**: `v3.0.0-DEMO-PORTAL`

---

## 1. Web Portal Access

You can access the live, glassmorphic **Web Credentials Hub** directly in your browser:

- 🌐 **URL**: `http://localhost:8000/demo-credentials/` or `https://your-domain.com/demo-credentials/`
- 🔑 **Default Password for All Roles**: **`EduOrbit@2026`**

The Web Credentials Hub provides **One-Click Auto Sign-In** and **Copy to Clipboard** buttons for every user role.

---

## 2. Complete Role Credentials Directory

| User Role | Username | Password | Role Email | Web Dashboard Route | Primary Modules Accessible |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. School Admin / Principal** | `admin.principal` | `EduOrbit@2026` | `admin.principal@eduorbit.com` | `/portal/dashboard/` | Executive Dashboards, Approvals, Global Setup, RBAC, BI Analytics |
| **2. Teacher / Educator** | `teacher.john` | `EduOrbit@2026` | `teacher.john@eduorbit.com` | `/portal/teacher/` | Daily Attendance Roll Call, LMS Courses, CBT Exams, Gradebook |
| **3. Parent / Guardian** | `parent.david` | `EduOrbit@2026` | `parent.david@eduorbit.com` | `/portal/parent/` | Multi-Child Switcher, Fee Payments (Paystack/OPay), Report Cards |
| **4. Student** | `student.romeo` | `EduOrbit@2026` | `student.romeo@eduorbit.com` | `/portal/student/` | LMS Lessons & Homework, CBT Exams, Digital Library, Wallet |
| **5. Finance Officer / Accountant** | `finance.officer` | `EduOrbit@2026` | `finance.officer@eduorbit.com` | `/hr/finance/postings/` | Fee Setup, Invoices, Over-the-Counter Payments, General Ledger |
| **6. HR Officer / Payroll Manager** | `hr.admin` | `EduOrbit@2026` | `hr.admin@eduorbit.com` | `/hr/admin/dashboard/` | Employee Directory, Onboarding, Leave Approvals, Monthly Payroll |
| **7. Library Staff / Librarian** | `librarian.mary` | `EduOrbit@2026` | `librarian.mary@eduorbit.com` | `/library/api/v1/` | Accession Catalog, Barcode Circulation Issues/Returns, Fines |
| **8. Hostel Warden / Housing** | `warden.sam` | `EduOrbit@2026` | `warden.sam@eduorbit.com` | `/hostel/api/v1/` | Hostel Blocks, Room & Bed Allocations, Nightly Attendance |
| **9. Transport Officer** | `transport.officer` | `EduOrbit@2026` | `transport.officer@eduorbit.com` | `/transport/api/v1/` | Vehicle Fleet, Driver Assign, Route Stops, GPS Dispatch |
| **10. School Nurse / Clinic** | `nurse.sarah` | `EduOrbit@2026` | `nurse.sarah@eduorbit.com` | `/clinic/api/v1/` | Student Health EHR, Sick Bay Visits, Pharmacy, Termii SMS Alerts |
| **11. SaaS Platform Super Admin** | `super.admin` | `EduOrbit@2026` | `super.admin@eduorbit.com` | `/administration/dashboard/` | Multi-Tenant SaaS Provisioning, Billing Engine, Feature Flags |
| **12. Exam Officer / CBT Lead** | `exam.officer` | `EduOrbit@2026` | `exam.officer@eduorbit.com` | `/eae/api/v1/` | Question Banks, CBT Exam Sessions, Auto-Marking Engine |

---

## 3. How to Sign In via Web

### Method A: Using the Interactive Web Portal Hub
1. Navigate to `/demo-credentials/` in your browser.
2. Locate your desired role card (e.g. *Teacher, Parent, Finance Officer*).
3. Click **Auto Sign-In** to automatically authenticate and land directly on that role's dashboard.

### Method B: Standard Sign-In Form
1. Navigate to `/identity/login/`.
2. Enter the **Username** (e.g. `teacher.john`) and Password `EduOrbit@2026`.
3. Click **Sign In**. The intelligent role router will automatically redirect you to the appropriate dashboard interface.
