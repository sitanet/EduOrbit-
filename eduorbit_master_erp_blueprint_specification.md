# EduOrbit Enterprise ERP — Master Architecture Blueprint & Ecosystem Specification

> **Document ID**: `EDU-ERP-BLUEPRINT-2026`  
> **Release Version**: `v1.0.0-MASTER-BLUEPRINT`  
> **Target Date**: July 27, 2026  
> **Architecture Level**: Enterprise Multi-Tenant SaaS ERP Ecosystem Architecture

---

## 1. Executive Summary & Ecosystem Vision

**EduOrbit ERP** is an enterprise-grade, multi-tenant SaaS Educational Resource Planning (ERP) platform engineered for K-12 school networks, university systems, and corporate education groups.

Built on Clean Architecture with Python 3.12, Django 5.x, PostgreSQL 16, Redis 7, Celery, and HTMX/Alpine.js visual portals, EduOrbit unifies 4 major enterprise product suites:
1. **Core Platform Shared Infrastructure**
2. **Academic Suite** (SIS, Admissions, Academics, Examination, CBT, Timetable, Student Attendance, Discipline, Graduation)
3. **Finance Suite** (Billing, Fees, Student Wallet, Payroll, Double-Entry Accounting, Assets, Procurement)
4. **People Suite** (HRMS ✓ Locked `v1.1.0`, Parent Portal, Staff Portal, Student Portal)

---

## 2. EduOrbit Master ERP Ecosystem Tree

```
EduOrbit ERP
│
├── Core Platform (Shared Platform Foundation)
│   ├── Identity & IAM (Unified User / Role / RBAC)
│   ├── Multi-Tenant Engine (Row Isolation & Schema Boundaries)
│   ├── Unified Notification Engine (Email, SMS, Push, In-App)
│   ├── Enterprise Report Engine (PDF, CSV, Excel Exporter)
│   ├── Shared Workflow Engine (Multi-Tier Approval Chains)
│   ├── Document Management System (Encrypted Cloud Storage)
│   ├── Global Search Engine (Cross-Domain Search Bar)
│   └── Audit Logging Service (ISO 27001 Audit Trails)
│
├── Academic Suite
│   ├── Student Information System (SIS) [Master Student Profile & Enrollment]
│   ├── Admissions & CRM (Applicant Portal & Registration)
│   ├── Academics & Curriculum (Syllabus, Subjects, Classes, Arms)
│   ├── Examination & Grading (Continuous Assessment & Report Cards)
│   ├── Computer-Based Testing (CBT Engine & Question Bank)
│   ├── Timetable & Scheduling (Auto-Scheduling & Room Allocation)
│   ├── Student Attendance (Daily Roll-Call & Biometric Check-In)
│   ├── Student Discipline & Merit (Infraction Records & Merit Badges)
│   └── Graduation & Alumni (Transcripts, Certificates & Alumni Portal)
│
├── Finance Suite
│   ├── Billing & Invoice Engine (Tuition Invoicing & Term Billing)
│   ├── Fee Structure Manager (Discounts, Scholarships & Bursaries)
│   ├── Student Digital Wallet (Prepaid Canteen & Library Wallet)
│   ├── Payroll Engine (HRMS Integrated PITA PAYE & Pension 8%) ✓
│   ├── Double-Entry Accounting (General Ledger, Debits & Credits)
│   ├── Asset & Facility Management (Equipment & Campus Depreciation)
│   └── Procurement & Requisitions (Purchase Orders & Vendors)
│
└── People Suite
    ├── HRMS ✓ (Locked v1.1.0 Enterprise Employee Onboarding & Payroll)
    ├── Parent Portal (Mobile-First Guardian Dashboard & Fee Payments)
    ├── Staff Portal (Teacher Workstation & Lesson Plan Manager)
    └── Student Portal (Learner LMS, Homework & Exam Interface)
```

---

## 3. Suite-by-Suite Architectural Specifications

### 3.1 Core Platform Shared Infrastructure
- **Identity & RBAC**: Centralized `User` model with dynamic permission groups across HR, SIS, Finance, and Portals.
- **Multi-Tenant Engine**: Row-level `tenant_id` database filtering enforcing strict tenant data isolation.
- **Notification Engine**: `UnifiedNotificationService` in `backend/apps/core/services/notifications.py` handling multi-channel alerts.
- **Transactional Outbox**: Atomic event publishing for background Celery event processing.

### 3.2 Academic Suite
- **Student Information System (SIS)**: Central student entity linking academic history, guardian contacts, class arms, attendance, and fee status.
- **Admissions Engine**: Online applicant registration, document verification, entrance exam scoring, and automated SIS enrollment.
- **Examination & CBT Engine**: Automated grading, continuous assessment (CA 30% / Exam 70%), report card generation, and real-time online CBT testing.

### 3.3 Finance Suite
- **Billing & Fee Structure Engine**: Invoicing, term fee schedules, partial payments, scholarships, and bursary allocations.
- **Double-Entry General Ledger**: Real-time integration with HR Payroll and Fee collections ensuring $\text{Total Debits} = \text{Total Credits}$.

### 3.4 People Suite
- **HRMS (`v1.1.0-RELEASE`)**: Complete employee lifecycle, 8-step wizard with Dojah KYC, Nigerian PAYE tax, 8% Pension, and dynamic workflows.
- **Portals**: Dedicated HTMX + Alpine.js web portals for Parents, Teachers/Staff, and Students.

---

## 4. Implementation Phasing Roadmap

```
  Phase 1 & 2 (DONE) ──>     Phase 3 (CURRENT)     ──>      Phase 4 (NEXT)        ──>       Phase 5
  - HRMS v1.1.0 Lock     - Master ERP Blueprint     - Student Info System (SIS)    - Academic & CBT Suite
  - Core Foundation      - Architecture Specs       - Admissions Engine            - Finance & Invoicing
```
