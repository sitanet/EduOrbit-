# EduOrbit ERP v1.3.0 — Academic Operations (Release 1) Module Lock Specification

> **Module Status**: `FROZEN & LOCKED (v1.3.0-RELEASE-1)`  
> **Release Target**: `v1.3.0-RELEASE-1`  
> **Target Date**: July 27, 2026  
> **Scope**: Academic Structure, Subjects, Departments, Class Arms, Credit Hours, Subject Offerings, & Curriculum Mapping.

---

## 1. Executive Summary & Module Freeze Milestone

Phase 4 Release 1 of **EduOrbit ERP v1.3.0 — Academic Operations** has been implemented, tested, verified, and locked under `v1.3.0-RELEASE-1`.

---

## 2. Implemented & Verified Components

1. **Curriculum & Subject Catalog Engine** (`backend/apps/academic/models.py`):
   - `Curriculum`, `SubjectCategory`, `Subject`, `SubjectOffering`, `Department`, `EducationLevel`, `AcademicLevel`, `AcademicClass`.
2. **Academic Catalog Service** (`backend/apps/academic/services/catalog.py`):
   - `AcademicCatalogService.create_subject()` (Subject catalog creation with credit units).
   - `AcademicCatalogService.map_subject_to_class()` (Mapping active subjects to class arms).
   - `AcademicCatalogService.get_class_curriculum_workload()` (Credit unit and workload computation per class).

---

## 3. Automated Test Verification Results

Executing `scratch/run_academic_catalog_test.py` verified 100% test pass rate:
```bash
=== Running Academic Operations Catalog Test Battery ===
PASSED: test_create_subject_and_class_mapping

=== ALL ACADEMIC CATALOG TESTS PASSED SUCCESSFULLY! ===
```
- **System Check Output**: `python manage.py check` -> `System check identified no issues (0 silenced).`
