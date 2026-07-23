# People Management Core (PMC) System Documentation

This document describes the structure, role assignments, family relationship links, and demographic tracking engines of the **people** core module.

---

## 1. Polymorphic Person Model & Role Assignments
To prevent duplicate profile data (names, emails, physical locations) when an individual occupies multiple roles (e.g. parent and teacher), demographics are stored in a single base table:
```
[ Person (Core Profile Details) ]
       │
       ├── Assigned via [ PersonRole ] ──> Maps to School/Campus (student, teacher, parent, staff)
       ▼
[ StudentProfile / TeacherProfile / StaffProfile / ParentProfile ]
```

---

## 2. Normalized Contacts & Emergency Matrix
Demographics are normalized into clean associated tables:
- **EmailAddress**: Multiple email mappings with verified/primary flags.
- **PhoneNumber**: Multi-phone numbers.
- **PhysicalAddress**: Address history trackers.
- **EmergencyContact**: Priority emergency contacts.

---

## 3. Medical Profile & History Timeline
- `MedicalProfile`: Captures static properties (blood group, genotype).
- `MedicalHistory`: Logs chronic items, allergies, and clinical visits history.

---

## 4. Family Relationship Engine
- **FamilyRelationship**: Links students to parents/guardians with parameters:
  - Custody/Legal guardian authorization indicator.
  - Pickup authorizations flags.
  - School fee payment responsibility percentages.
  - Emergency contact priority order.

---

## 5. REST APIs
Endpoints are mounted under `/people/api/v1/`:
- `GET/POST /people/`: Retrieve/Create core profiles.
- `GET /people/search/?q=`: Search query on names or person numbers.
- `POST /people/roles/`: Manage assignments.
- `POST /people/relationships/`: Links parent-child relationships.
