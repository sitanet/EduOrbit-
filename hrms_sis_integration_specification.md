# EduOrbit ERP — HRMS & SIS Cross-Module Integration Specification

> **Document ID**: `EDU-HRMS-SIS-INT-2026`  
> **Release Target**: `v1.2.0-INTEGRATION`  
> **Target Date**: July 27, 2026  
> **Architecture Level**: Cross-Domain Service Layer & Event Integration Specification

---

## 1. Executive Summary

Phase 7 establishes **Cross-Module Integration between HRMS and SIS**.

While HRMS and SIS operate as independent domain modules, they communicate through a clean, decoupled service layer (`HRMSSISIntegrationService` in `backend/apps/core/services/hrms_sis_integration.py`) and transactional domain events.

---

## 2. Integrated Workflows & Contract Interfaces

### 2.1 HR Employee → Teacher Profile Mapping
- **Service**: `HRMSSISIntegrationService.map_employee_to_teacher(employee_profile, teaching_license_number)`
- **Function**: Automatically provisions a `TeacherProfile` linking to the same core `Person` entity as the HR `EmployeeProfile`.

### 2.2 Leave → Substitute Teacher Coverage Workflow
- **Service**: `HRMSSISIntegrationService.assign_substitute_teacher(leave_request, substitute_teacher_person)`
- **Function**: Triggers substitute teacher coverage and dispatches multi-channel notifications when a class teacher takes approved leave.

### 2.3 SIS Class Workload → HR Payroll Allowances
- **Service**: `HRMSSISIntegrationService.calculate_teaching_allowance(employee_profile, assigned_class_count)`
- **Function**: Calculates extra teaching workload pay (₦15,000 per extra class arm above 3 assigned classes) for HR Payroll computation.

---

## 3. Automated Test Verification Results

Executing `scratch/test_phase7_integration.py` passed with 100% success rate:
```bash
=== Running Phase 7 HRMS-SIS Cross-Module Integration Test Battery ===
PASSED: Employee -> Teacher Profile Mapping -> success
PASSED: Teaching Allowance -> NGN 30,000.00 for 5 Classes
PASSED: Substitute Teacher Assigned -> Jean Grey replacing Charles Xavier

=== ALL PHASE 7 INTEGRATION TESTS PASSED SUCCESSFULLY! ===
```
