# Enterprise Facilities, Maintenance & Work Orders (EFMWO) Documentation

This document describes the building maps, room configurations, physical facilities appliances, maintenance work requests, work orders dispatch, preventive maintenance plans, inspections, and utility meter readings of the **facilities** app.

---

## 1. Physical Infrastructure
- **Building**: Site name, code, coordinates.
- **Floor**: Vertical structure divisions.
- **Room**: Classrooms, labs, or hostels room parameters.
- **Facility**: Specific physical appliances (AC units, water pumps).

---

## 2. Work Order Engine
- **WorkRequest**: Problems reporting (description, priority).
- **WorkOrder**: Lifecycle tracking (assigned, in_progress, completed, closed).
- **WorkLog**: Audit history steps.

---

## 3. Preventive Maintenance & Utilities
- **FacilityMaintenancePlan & FacilityMaintenanceSchedule**: Preventive servicing schedulers to resolve conflicts with Transport model names.
- **Inspection**: Cleanliness and safety audits.
- **UtilityMeter & UtilityReading**: Daily resource usage inputs (electricity, water).

---

## 4. REST APIs
Endpoints are mapped under `/facilities/api/v1/`:
- `GET/POST /facilities/buildings/`: Building list.
- `GET/POST /facilities/rooms/`: Rooms list.
- `GET/POST /facilities/workorders/`: Issued work orders.
