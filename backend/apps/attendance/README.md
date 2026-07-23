# Attendance Management (ATM) System Documentation

This document describes the structure, offline synchronization pipelines, adjustments workflows, ECE early childhood pickups, and AI risk stubs of the **attendance** app.

---

## 1. Generic Attendance Engine
To prevent duplicating logging logic for students, teachers, transport, and hostels, the system routes all attendance marks through a single polymorphic table referencing the general Person entity:
```
[ AttendanceSession ] ──> Maps LessonInstance or Roll Call contexts
       │
       ▼
[ AttendanceRecord ] ──> Links unified [ Person ] profile to [ AttendanceStatus ] codes
```

---

## 2. Attendance Policies & Hardware Integration
- **AttendancePolicy**: Scoped by school, defining min attendance thresholds (e.g. 75.0%) and late grace periods.
- **AttendanceDevice**: Stash for terminal readers (RFID, Facial recognition gates) syncing data.

---

## 3. Early Childhood Education (ECE) Pickups
- **ParentPickup**: Checks student departures mapping pickup timestamps, authorized persons (Family Relationship pointer), and verification pins/QR validations.

---

## 4. Offline Syncing & Conflict resolution
- **OfflineSyncQueue**: Client check-in cache logs containing client-generated UUID keys to prevent duplicates, resolving conflicts via client-side timestamps.

---

## 5. REST APIs
Endpoints are mounted under `/attendance/api/v1/`:
- `GET /attendance/records/`: Retrieval of logs.
- `POST /attendance/corrections/`: Request adjustment.
- `POST /attendance/sync/`: Syncs offline caches.
