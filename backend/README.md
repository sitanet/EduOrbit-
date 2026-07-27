# EduOrbit Enterprise HRMS v1.1.0 — Master Documentation Suite & System Index

> **Release Version**: `v1.1.0-RELEASE`  
> **Release Date**: July 27, 2026  
> **Module Status**: `FROZEN & LOCKED`  
> **Overall Production Readiness Score**: `100% PRODUCTION READY`

---

## 1. Documentation Suite Hierarchy & Entry Point Map

Welcome to the master documentation entry point for **EduOrbit HRMS v1.1.0 Enterprise Edition**. This suite provides role-tailored operational guides, technical architecture specifications, REST API references, and formal release governance audit reports.

```
                                  [ README.md ]
                     (Master Entry Point & Navigation Index)
                                       │
      ┌────────────────────────────────┼────────────────────────────────┐
      ▼                                ▼                                ▼
[Role User Guides]           [Technical Specifications]       [Governance & Audit Reports]
 ├─ hr_user_guide.md          ├─ hr_architecture_guide.md       ├─ HR_MODULE_LOCK_v1.1.0.md
 ├─ hr_admin_guide.md         ├─ hr_api_documentation.md        ├─ hr_phase6_acceptance_report.md
 ├─ hr_payroll_guide.md       ├─ hr_production_checklist.md     ├─ hr_v110_real_browser_audit.md
 ├─ hr_manager_guide.md       └─ hr_demo_walkthrough.md         └─ hr_documentation_quality_audit.md
 └─ hr_employee_guide.md
```

---

## 2. Recommended Reading Order by Audience Role

| Your Role in EduOrbit | Primary Recommended Reading Order | Key Functional Focus Areas |
| :--- | :--- | :--- |
| **System Administrator & HR Director** | 1. [hr_admin_guide.md](file:///c:/Users/user/Desktop/Development/SMS/hr_admin_guide.md)<br>2. [hr_user_guide.md](file:///c:/Users/user/Desktop/Development/SMS/hr_user_guide.md)<br>3. [hr_production_checklist.md](file:///c:/Users/user/Desktop/Development/SMS/hr_production_checklist.md) | Org Hierarchy, 8-Step Onboarding Wizard, Employee Number Patterns, Sub-Module Flags. |
| **Payroll Specialist & Finance Officer** | 1. [hr_payroll_guide.md](file:///c:/Users/user/Desktop/Development/SMS/hr_payroll_guide.md)<br>2. [hr_user_guide.md](file:///c:/Users/user/Desktop/Development/SMS/hr_user_guide.md)<br>3. [hr_api_documentation.md](file:///c:/Users/user/Desktop/Development/SMS/hr_api_documentation.md) | Monthly Payroll Generation, PITA CRA PAYE Tax, Pension 8%, NHF 2.5%, Double-Entry GL. |
| **Department Manager / HOD** | 1. [hr_manager_guide.md](file:///c:/Users/user/Desktop/Development/SMS/hr_manager_guide.md)<br>2. [hr_user_guide.md](file:///c:/Users/user/Desktop/Development/SMS/hr_user_guide.md) | Team Portal, Leave Application Approval, Shift Lateness Review, Appraisal Ratings. |
| **Staff Member / Teacher** | 1. [hr_employee_guide.md](file:///c:/Users/user/Desktop/Development/SMS/hr_employee_guide.md)<br>2. [hr_user_guide.md](file:///c:/Users/user/Desktop/Development/SMS/hr_user_guide.md) | ESS Workspace, ⏰ Clock In/Out Terminal, Leave Applications, PDF Payslip Downloads. |
| **Enterprise Solution Architect** | 1. [hr_architecture_guide.md](file:///c:/Users/user/Desktop/Development/SMS/hr_architecture_guide.md)<br>2. [HR_MODULE_LOCK_v1.1.0.md](file:///c:/Users/user/Desktop/Development/SMS/HR_MODULE_LOCK_v1.1.0.md)<br>3. [hr_api_documentation.md](file:///c:/Users/user/Desktop/Development/SMS/hr_api_documentation.md) | 6-Layer Clean Architecture, Multi-Tenancy Isolation, Outbox Bus, Encryption. |
| **DevOps & QA Lead** | 1. [hr_phase6_acceptance_report.md](file:///c:/Users/user/Desktop/Development/SMS/hr_phase6_acceptance_report.md)<br>2. [hr_production_checklist.md](file:///c:/Users/user/Desktop/Development/SMS/hr_production_checklist.md)<br>3. [hr_v110_real_browser_audit.md](file:///c:/Users/user/Desktop/Development/SMS/hr_v110_real_browser_audit.md) | Release Gates, SLA Benchmarks, 26 Route Crawl, Disaster Recovery, Production Lock. |

---

## 3. Quick Start Guide for System Operators

### 3.1 Local Environment Credentials & URLs
- **Web Application URL**: `http://127.0.0.1:8000`
- **Interactive User Manual**: `http://127.0.0.1:8000/hr/manual/`
- **Enterprise Onboarding Wizard**: `http://127.0.0.1:8000/hr/admin/onboarding/wizard/`

### 3.2 Demo Role Login Quick Table
| Role Code | Username | Default Password | Primary Portal Route |
| :--- | :--- | :--- | :--- |
| **HR Admin** | `hr.admin` | `Demo@2026` | `/hr/admin/dashboard/` |
| **Payroll Admin** | `payroll.admin` | `Demo@2026` | `/hr/payroll/` |
| **Department Manager** | `dept.manager` | `Demo@2026` | `/hr/manager/team/` |
| **Staff Member** | `staff.member` | `Demo@2026` | `/hr/ess/` |
| **Finance Officer** | `finance.officer` | `Demo@2026` | `/hr/finance/postings/` |

---

## 4. Master Cross-Reference Map of Artifacts

- 📄 **[hr_user_guide.md](file:///c:/Users/user/Desktop/Development/SMS/hr_user_guide.md)** — General user manual covering overall system functionality.
- 📄 **[hr_admin_guide.md](file:///c:/Users/user/Desktop/Development/SMS/hr_admin_guide.md)** — Administrator reference covering tenant setup, 8-Step Wizard, and Org Hierarchy.
- 📄 **[hr_payroll_guide.md](file:///c:/Users/user/Desktop/Development/SMS/hr_payroll_guide.md)** — Statutory payroll and double-entry GL accounting guide.
- 📄 **[hr_employee_guide.md](file:///c:/Users/user/Desktop/Development/SMS/hr_employee_guide.md)** — Employee Self-Service guide for attendance clocking and leave.
- 📄 **[hr_manager_guide.md](file:///c:/Users/user/Desktop/Development/SMS/hr_manager_guide.md)** — Manager Team portal guide for leave approvals and appraisal reviews.
- 📄 **[hr_api_documentation.md](file:///c:/Users/user/Desktop/Development/SMS/hr_api_documentation.md)** — REST API specification for KYC verification and draft auto-save.
- 📄 **[hr_architecture_guide.md](file:///c:/Users/user/Desktop/Development/SMS/hr_architecture_guide.md)** — Technical architecture specification covering clean layering and outbox pattern.
- 📄 **[hr_production_checklist.md](file:///c:/Users/user/Desktop/Development/SMS/hr_production_checklist.md)** — Infrastructure release hardening checklist.
- 📄 **[hr_demo_walkthrough.md](file:///c:/Users/user/Desktop/Development/SMS/hr_demo_walkthrough.md)** — 15-minute live demonstration script.
- 📄 **[hr_phase6_acceptance_report.md](file:///c:/Users/user/Desktop/Development/SMS/hr_phase6_acceptance_report.md)** — 18-chapter master release acceptance sign-off document.
- 📄 **[HR_MODULE_LOCK_v1.1.0.md](file:///c:/Users/user/Desktop/Development/SMS/HR_MODULE_LOCK_v1.1.0.md)** — 19-chapter master release freeze document.
- 📄 **[hr_v110_real_browser_audit.md](file:///c:/Users/user/Desktop/Development/SMS/hr_v110_real_browser_audit.md)** — Real browser acceptance crawl report across 26 routes.
- 📄 **[hr_documentation_quality_audit.md](file:///c:/Users/user/Desktop/Development/SMS/hr_documentation_quality_audit.md)** — Enterprise documentation quality and standards audit report.

---

## 5. Version History & Governance Policy

- **`v1.0.0` (Legacy Base)**: Core employee profile and simple leave request tracking.
- **`v1.1.0-RELEASE` (Current Release)**: Complete Enterprise Edition upgrade introducing 12-state lifecycle, 7-tier org hierarchy, position headcount management, 8-step wizard with pluggable Dojah KYC, AES-256 PII encryption, statutory Nigerian PAYE tax engine, double-entry GL ledger posting, and dynamic workflow designer.
- **Version Governance Policy**: `v1.1.x` patch series reserved for production hotfixes. New feature modules deferred to `v1.2.0`.
