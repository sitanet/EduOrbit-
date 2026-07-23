# Learning Management System (LMS) System Documentation

This document describes the structure, dynamic lesson-centric sequencing, DRM licensing constraints, and AI extension stubs of the **lms** app.

---

## 1. Lesson-Centric Hierarchy
To ensure all study guides align with scheduled classroom lessons, the LMS structure is split into three layers:
```
[ LearningModule ] ──> Groups term topics (e.g. Algebra I)
       │
       ▼
[ LearningUnit ] ──> Specific lesson steps (e.g. Quadratic Formulas)
       │
       ├── [ LearningContent ] ──> Reusable versioned assets (PDF, video, HTML)
       └── [ LearningActivity ] ──> Steps checkouts (reading, quizzes, homework)
```

---

## 2. Dynamic Learning Paths & Sequencing
- **LearningPath** & **LearningPathStep**: Allows teachers to chain modules together, creating prerequisite sequences. A student cannot start a step until the prerequisite is completed.

---

## 3. Student Progress & DRM Licensing
- **StudentProgress**: Tracks time spent, completion percentage, and sync status for offline usage.
- **ContentLicense**: Restricts downloads, sets expiration dates, and restricts access to specific classes.

---

## 4. REST APIs
Endpoints are mounted under `/lms/api/v1/`:
- `GET/POST /lms/modules/`: Manage course modules.
- `GET/POST /lms/units/`: Manage learning units.
- `GET/POST /lms/progress/`: Retrieve/save student progress.
