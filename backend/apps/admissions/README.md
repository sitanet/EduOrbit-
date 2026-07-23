# Admissions & Enrollment Management (AEM) System Documentation

This document describes the structure, applicant promotions, dynamic intakes, and forms engine configurations of the **admissions** module.

---

## 1. Applicant Mappings & Multiple Applications
To keep historically accurate records across academic terms, applicants are structured as distinct entities pointing back to a base Person demographic profile:
```
[ Person (Unified Profile) ]
       │
       ▼
[ Applicant (School-scoped) ] ──> Holds multiple [ AdmissionApplication ] records
```

---

## 2. Dynamic Forms & Section Fields Engine
AEM houses a generic dynamic forms parser allowing custom fields definitions per campaign intakes:
- **FormDefinition**: Form configuration headers.
- **FormSection**: Nested sections.
- **FormField**: Individual inputs parameters (e.g. checkbox, files) and validation rules.
- **FormSubmission**: JSON draft payload storage.

---

## 3. Admissions Workflow Steps & Offer Management
Applications progress through configurable steps (Application, Review, Interview, Decision, Offer, Enrollment):
- **ApplicationDocument**: Dynamic verification statuses (pending, approved, rejected).
- **AdmissionAssessment**: Entrance exams, oral screening, and scores tracking.
- **AdmissionOffer**: Offer issued, deadlines accepted, and conditional parameters.

---

## 4. Enrollment Promotion Service
`EnrollmentService.enroll_applicant()` runs inside a database transaction executing:
1. Promotes base `Person` profile to an active `StudentProfile`.
2. Assigns a generated student number code.
3. Automatically sets starting class limits and active school years.
4. Triggers the `student.enrolled` event log.

---

## 5. REST APIs
Endpoints are mounted under `/admissions/api/v1/`:
- `GET /admissions/campaigns/`: School campaigns listing.
- `GET /admissions/intakes/`: Cohorts intakes options.
- `GET /admissions/applications/`: Active review application list.
- `POST /admissions/enrollment/`: Enrolls applicant.
