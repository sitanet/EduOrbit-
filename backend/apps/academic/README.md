# Academic Configuration Engine (ACE) System Documentation

This document describes the structure, validation mechanics, grading engines, and dynamic promotion boundaries of the **academic** configuration module.

---

## 1. Academic Hierarchy & Scoping
To prevent configuration leaks between schools under the same corporate tenant group, all entities scope to an explicit school instance ForeignKey:
```
[ Tenant (Organization) ]
       │
       ▼ (Contains multiple schools)
[ School ] ──> Scopes [ AcademicYear, EducationLevel, AcademicClass, Subjects ]
```

- **EducationLevel**: Represents category structures (e.g. Primary, Secondary).
- **AcademicLevel**: Represents structural year steps (e.g. Primary 1, JSS 2).
- **AcademicClass**: Represents target classrooms instances (e.g. Primary 1 Gold).

---

## 2. Curriculum & Subjects Offerings Mappings
- Curricula are global references defining standard versions (e.g. Cambridge IGCSE 2024).
- **Subject**: Code, name, category, and credit units are mapped to a Curriculum.
- **SubjectOffering**: Relates subjects directly to active classes during a specific academic year.

---

## 3. Grading & Assessment Schemes
- **GradingScale**: Enforces boundary ranges (percentage or GPA values) assignable by Education Levels.
- **AssessmentComponent**: Allocates weighted configuration models (e.g., Assignment 10%, Project 30%, Final Exam 60%).

---

## 4. Rule-Based Promotion Policies
- **PromotionPolicy**: Allows schools to define criteria thresholds for automatic progression:
  - Minimum overall scores percentage.
  - Minimum subject passes counts.
  - Required minimum attendance percentage.

---

## 5. REST APIs
Endpoints are mounted under `/academic/api/v1/`:
- `GET /academic/settings/`: Resolves school defaults.
- `GET/POST /academic/years/`: Active/future academic cycles.
- `GET /academic/levels/`: Education levels.
- `GET /academic/subjects/`: Course subject registry.
