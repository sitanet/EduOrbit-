# Student Lifecycle Management (SLM) System Documentation

This document describes the structure, promotion engine, historical placements, and state machine transitions of the **students** module.

---

## 1. State Machine Lifecycle States
To manage the operational lifecycle of a student from enrollment to alumni, transitions are governed by a reusable State Machine:
```
[ Pending ] ──> [ Active ] ──> [ Suspended / Expelled ] ──> [ Archived ]
                     │
                     ▼
             [ Graduated ] ──> [ Alumni ]
```

- Status history logs are stored dynamically under `StudentStatusHistory`.

---

## 2. Placements & Promotion Engines
- **AcademicPlacementHistory**: Retains historical tracking (never overwritten) linking student records to class levels, academic terms, boarding houses, and branches.
- **ClassPromotion**: Logs automatic or manual promotions, storing old vs new class mappings and promotion dates.
- **StudentTransfer**: Logs details of internal campus or external school transfers.

---

## 3. Demerit, Merits & Timeline Logs
- **StudentDiscipline**: Registers demerits/merits and recorded points.
- **StudentTimeline**: Single chronological feed aggregating all student life events (promotions, warnings, awards).
- **StudentNote**: Privacy-controlled staff remarks.

---

## 4. REST APIs
Endpoints are mounted under `/students/api/v1/`:
- `GET /students/placements/`: Placement history registry.
- `POST /students/promotions/`: Promotes student.
- `GET /students/<uuid>/timeline/`: Returns timeline events.
