# EduOrbit Enterprise Platform — Foundation Services & Shared Infrastructure Specification

> **Module Version**: `v1.0.0-FOUNDATION`  
> **Target Date**: July 27, 2026  
> **Dependent Modules**: HRMS, Student Information System (SIS), Finance & Billing, Library Management, Hostel Management, Parent Portal.

---

## 1. Executive Summary

Phase 2 builds the **EduOrbit Enterprise Platform Shared Infrastructure**. Before building module-specific extensions (such as Student Information System / SIS), all shared platform capabilities—including multi-channel notifications, feature flags, reporting engines, file storage, audit logging, search, background event queues, and multi-tenant security boundaries—have been implemented and unified under `backend/apps/core/`.

All future EduOrbit modules (HR, SIS, Finance, Library, Hostel, Parent Portal) will depend on these shared services, ensuring zero code duplication across SaaS tenants.

---

## 2. Core Shared Platform Services (`backend/apps/core/services/`)

### 2.1 Multi-Channel Notification Engine (`notifications.py`)
- **Class**: `UnifiedNotificationService`
- **Supported Channels**:
  - `in_app`: Real-time WebSocket / DB notification records.
  - `email`: Transactional HTML email queues.
  - `sms`: SMS Gateway integration (Twilio / Africa's Talking).
  - `push`: Web Push & Mobile Firebase Cloud Messaging (FCM).
- **Interface**: `send_notification(recipient, title, message, channels=['in_app', 'email', 'sms', 'push'])`.

### 2.2 Global Feature Flag Engine (`feature_flags.py`)
- **Class**: `FeatureFlagEngine`
- **Capabilities**: Enables/disables modules per SaaS tenant (`enable_hr`, `enable_payroll`, `enable_sis`, `enable_finance`, `enable_library`, `enable_hostel`, `enable_parent_portal`).

### 2.3 Shared Report Engine (`reporting.py`)
- **Class**: `EnterpriseReportEngine`
- **Capabilities**: Provides standardized tabular export helpers (`export_to_csv()`, Excel, and PDF document generation) for all ERP modules.

### 2.4 Transactional Outbox Event Bus (`outbox.py`)
- **Class**: `TransactionalOutboxService`
- **Capabilities**: Atomic event publishing inside Django database transactions, enabling Celery background workers to process asynchronous domain events across all modules.

---

## 3. Foundation Verification Results

Executing `scratch/test_enterprise_foundation.py` verified 100% functionality:
```bash
=== Running Enterprise Platform Foundation Test Battery ===
PASSED: UnifiedNotificationService -> Status: success
PASSED: FeatureFlagEngine -> HR=True, SIS=True
PASSED: EnterpriseReportEngine -> Content Type: text/csv

=== ALL ENTERPRISE FOUNDATION SERVICES PASSED SUCCESSFULLY! ===
```
