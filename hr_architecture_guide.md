# EduOrbit HRMS v1.1.0 — Technical Architecture Guide (`hr_architecture_guide.md`)

> **Architectural Level**: Enterprise Domain Architecture  
> **Target Audience**: Solution Architects, Senior Engineers, Technical Leads

---

## 1. Domain Architecture & Layering

```
  [UI / Templates]   ──> HTMX + Alpine.js + Tailwind Glassmorphic Views
  [Web Controllers] ──> Views in backend/apps/hr/views_web.py
  [REST API Layer]   ──> API Views in backend/apps/hr/api/
  [Service Layer]    ──> KYCProvider, Readiness, EmployeeNumberGenerator, DuplicateDetector
  [Domain Models]    ──> EmployeeProfile, JobPosition, CompensationHistory, ApprovalWorkflow
  [Data Infrastructure] ─> PostgreSQL (AES-256 Fernet), Redis, Celery, Outbox
```

---

## 2. Multi-Tenancy & Data Isolation

All models inherit from `TenantBaseModel` (or `PlatformBaseModel`). Dynamic schema selection and row-level `tenant_id` filtering guarantee complete SaaS data isolation across schools.

---

## 3. Transactional Outbox Event Bus Pattern

All domain mutations emit events to `core_transactionaloutbox` inside atomic transactions:
- `employee.created`
- `employee.nin_verified`
- `payroll.posted`

Events are processed asynchronously by Celery workers to decouple domain side-effects.
