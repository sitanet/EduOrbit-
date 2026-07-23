# Enterprise Hostel & Residential Management (EHRM) Documentation

This document describes the residential buildings structures, room capacity lists, bed allocations, nightly curfew roll-calls, visitors, and hygiene inspection logs of the **hostel** app.

---

## 1. Residential Schema
- **Hostel**: Residential buildings and gender guidelines.
- **HostelBlock**: Wing/block subdivisions.
- **HostelRoom**: Capacity and floor.
- **HostelBed**: Specific bed tracking codes.

---

## 2. Leases & Curfews
- **BedAllocation**: Connects students to specific beds with lease start/end dates.
- **HostelRollCall**: Nightly check-in curfew logs (present, absent, excused).

---

## 3. Visitors & Hygiene Checks
- **HostelVisitor**: Guest tracking details.
- **HostelIncident**: Behavior violations logs.
- **RoomInspection**: Hygiene score audits.

---

## 4. REST APIs
Endpoints are mapped under `/hostel/api/v1/`:
- `GET/POST /hostel/allocations/`: Bed assignments management.
- `GET/POST /hostel/rollcall/`: Nightly check-ins.
- `GET/POST /hostel/visitor/`: Guest logging.
