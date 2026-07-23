# Enterprise Assessment Engine (EAE) System Documentation

This document describes the structure, assessment generation blueprints, attempts tracking, proctor security logging, and manual rubric workflows of the **eae** app.

---

## 1. Multi-Channel Assessment Architecture
The EAE is designed to be delivery-agnostic. Assessments are structured uniformly, while the delivery channel (CBT, paper exams, orals, practicals) acts as a rendering wrapper:
```
[ AssessmentBlueprint ] ──> Dynamic generation rules
       │
       ▼
[ Assessment ] ──> The examination definition
       │
       ├── [ AssessmentSection ] ──> Partition weights (Section A, Section B)
       └── [ AssessmentAttempt ] ──> Student test execution log
```

---

## 2. Proctoring Security
- **ProctorLog**: Tracks suspicious client events (tab switches, exit full-screen attempts, copy-paste) during active sessions.

---

## 3. Marking Engine & Rubrics
- **Auto-Marking**: MCQ, true-false, and matching are graded automatically.
- **Manual Rubric-Marking**: Essay questions are routed to evaluation queues checking criteria grades in `RubricCriteria`.

---

## 4. REST APIs
Endpoints are mounted under `/eae/api/v1/`:
- `GET/POST /eae/questions/`: Manage question banks.
- `GET/POST /eae/assessments/`: Setup examinations.
- `GET/POST /eae/attempts/`: Retrieve or start attempts.
- `POST /eae/attempts/<attempt_uuid>/automark/`: Commit exam answers and trigger score caching.
