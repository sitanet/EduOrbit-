# Enterprise Clinic, Health & Medical Management (ECHM) Documentation

This document describes the clinic registries, patient profiles, clinical visits consultation triage logs, drug catalog prescriptions, sickbay admissions, and vaccination logs of the **clinic** app.

---

## 1. Registry & Workflows
- **Clinic**: School sickbays or clinic buildings.
- **PatientProfile**: HIPAA-compliant patient index pointing back to base `Person`.
- **Appointment**: Scheduled doctor/nurse slots.
- **ClinicVisit**: Logs patient consultations, symptoms, diagnoses.

---

## 2. Pharmacy & Sick Bay
- **Drug & DrugBatch**: Pharmacy inventory stock batch logs with expiry dates.
- **Prescription**: Medication administration instructions.
- **Ward & SickBayAdmission**: In-patient sickbay occupancy registers.
- **Vaccination**: Immunizations history schedules.

---

## 3. REST APIs
Endpoints are mapped under `/clinic/api/v1/`:
- `GET/POST /clinic/patients/`: Patient profiles registry.
- `GET/POST /clinic/appointments/`: Appointment booking slot registers.
- `GET/POST /clinic/visits/`: Clinical consultation triage logs.
