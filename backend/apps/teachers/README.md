# Teacher Workspace Core (TWC) System Documentation

This document describes the structure, curriculum mapping layers, lesson delivery instance trackers, and AI extensions stubs of the **teachers** app.

---

## 1. Curriculum & Four-Layer Planning Hierarchy
To preserve termly mappings and support weekly lesson generation, the planning framework uses four layers:
```
[ Curriculum (Cambridge/Nigerian Versioned) ]
                     │
                     ▼
             [ SchemeOfWork ] ──> Scoped by school, year, period, and level
                     │
                     ▼
               [ WeeklyPlan ] ──> Derived week-by-week
                     │
                     ▼
               [ LessonPlan ] ──> Specific objective details and plan versionings
```

---

## 2. Lesson Instance & Delivery Lifecycle
Timetable entries map to actual classroom events on specific days using a decoupled structure:
- **LessonInstance**: Ties a `Schedule` (Timetable slot) to a `LessonPlan` on a specific calendar Date.
- **LessonDelivery**: Tracks progress through states (Planned, Started, Completed, Cancelled, Rescheduled).

---

## 3. Teaching Journals & Student Observations
- **StudentObservation**: Captures academic performance, behaviour, and welfare remarks, and pushes notifications directly to the student's timeline.
- **TeachingJournal**: Retains daily teacher summaries, reflections, and topics covered.
- **Assignment**: Creates homework, project, and reading assignment definitions.

---

## 4. REST APIs
Endpoints are mounted under `/teachers/api/v1/`:
- `GET /teachers/curricula/`: Curricula listings.
- `GET/POST /teachers/lesson-plans/`: Lesson plan registry.
- `GET/POST /teachers/assignments/`: Assignment tasks creation.
- `POST /teachers/observations/`: Record student remarks.
