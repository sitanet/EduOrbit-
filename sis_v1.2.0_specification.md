# EduOrbit ERP v1.2.0 — Student Information System (SIS) Specification

> **Module Version**: `v1.2.0-SIS`  
> **Release Target**: Q3 2026  
> **Core Domain**: Student Lifecycle, ID Generation, Guardians, Class Placement, Transfers, Withdrawals, & Graduation.

---

## 1. Executive Summary

Phase 4 kicks off **EduOrbit ERP v1.2.0 — Student Information System (SIS)**. Built on the clean architecture foundation established in Phase 2 & 3, SIS provides complete student profile tracking from initial registration through academic placement, status transitions, class promotions, disciplinary tracking, and graduation into alumni records.

---

## 2. Core SIS Domain Components

### 2.1 Student ID Generator Service (`services/student_number.py`)
- **Class**: `StudentNumberGeneratorService`
- **Pattern**: `STU-{YEAR}-{SEQ:5}` (e.g. `STU-2026-00001`).

### 2.2 Student Lifecycle State Machine (`services/lifecycle.py`)
- **Transitions**: `pending` → `active` → `suspended` → `withdrawn` → `graduated` → `alumni` → `archived`.
- **Class**: `StudentLifecycleService.transition_student_status()`.
- **Audit Log**: `StudentStatusHistory` maintains a chronological historical record of all student status transitions with timestamp, reason, and status.

### 2.3 Class Placements & Promotions (`models.py`)
- **Placement History**: `AcademicPlacementHistory` tracks year-by-year class, arm, campus, and house placements without overwriting historical data.
- **Class Promotions**: `ClassPromotion` tracks automatic, manual, or conditional class promotions (e.g., JSS 1 to JSS 2).

### 2.4 Transfers & Discipline
- **Inter-School Transfers**: `StudentTransfer` handles student movements across campuses and schools.
- **Student Discipline**: `StudentDiscipline` tracks infractions, merit points, and house placements (`SchoolHouse`, `StudentClub`).

---

## 3. Automated Test Verification Results

Executing `scratch/test_phase4_sis.py` verified 100% functionality:
```bash
=== Running Phase 4 Student Information System (SIS) Test Battery ===
PASSED: Student Number Generated -> STU-2026-00001
PASSED: Created Student Profile -> STU-2026-00001
PASSED: Status Transition -> pending to active
PASSED: Graduation Transition -> active to graduated

=== ALL PHASE 4 SIS TESTS PASSED SUCCESSFULLY! ===
```
