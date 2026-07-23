# Timetable & Scheduling Engine (TSE) System Documentation

This document describes the structure, validation mechanics, conflict engines, and dynamic substitutions of the **timetable** core module.

---

## 1. Generalized Scheduling Architecture
To support scheduling academic lessons, exams, CBT blocks, and parent meetings under a single backend framework, the TSE isolates the structural concept of a Lesson from its scheduled placement in the timeline:
```
[ BellSchedule ] ──> Holds multiple [ TimeSlot ] ranges
[ Resource ] ──> Mapped locations (Classrooms, labs, sports fields)
[ Lesson ] ──> Subject-Teacher-Class requirement definitions
                                 │
                                 ▼
                     [ Schedule (Base Entity) ]
```

---

## 2. Dynamic Bell Schedules
- **BellSchedule**: Manages distinct timing configurations per education levels.
- **TimeSlot**: Sub-period timestamps (e.g. 08:00 - 08:40, Break Period toggles).

---

## 3. Conflict Detection Engine
The system performs pre-save validation before committing a `Schedule` or booking a `Resource`:
- **Teacher Overlap**: Prevents a teacher from being assigned to multiple classes simultaneously.
- **Room Overlap**: Prevents multiple classes from occupying the same facility slot.
- Overlaps register automatically in `ConflictReport` logs for audit trails.

---

## 4. REST APIs
Endpoints are mounted under `/timetable/api/v1/`:
- `GET /timetable/api/v1/schedules/resources/`: Active room listings.
- `GET/POST /timetable/api/v1/schedules/`: Retrieve schedules or create lessons with conflict detection.
- `GET /timetable/api/v1/schedules/conflicts/`: Conflicts audit trails listing.
