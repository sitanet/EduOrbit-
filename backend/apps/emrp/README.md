# Enterprise Examination Management & Results Processing (EMRP) Documentation

This document describes the structure, examinations sessions, scheduling, dynamic grading formulas, broadsheet analytics, and audit corrections of the **emrp** app.

---

## 1. Examination Lifecycle Architecture
The EMRP module manages the orchestration of results computation and workflows. It integrates with EAE but contains separate entities:
```
[ ExamSession ] ──> Groups exams under AcademicYear
       │
       ▼
[ Examination ] ──> Official exam header
       │
       ├── [ ExaminationPaper ] ──> Links EAE Assessment
       └── [ ExamResult ] ──> computed points, grade, and GPAs
```

---

## 2. Dynamic Grading Formula Engine
- **GradingFormula**: Enables school-specific weighted calculations (e.g. `raw_score * 0.7 + 30`) to compute official scores dynamically.

---

## 3. Audit Corrections & Versioning
- **ResultVersion**: Retains previous marks history dynamically during corrections.
- **ResultCorrection**: Formally tracks alteration reasons and requesters.

---

## 4. REST APIs
Endpoints are mounted under `/emrp/api/v1/`:
- `GET/POST /emrp/results/`: Retrieve or calculate final scores.
- `GET /emrp/exams/<exam_uuid>/broadsheet/`: Get cohort score averages.
- `GET /emrp/promotions-preview/`: Preview candidate promotional indicators.
