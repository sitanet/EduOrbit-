# Enterprise Human Resources & Payroll Management (HRPM) Documentation

This document describes the structure, employee lifecycle states, recruitment pipeline, leave requests, and payroll calculations of the **hr** app.

---

## 1. Employee Profile Lifecycle
The HRPM app extends the PMC base Person table with a dedicated child entity (`EmployeeProfile`) to isolate staff details without duplication:
```
[ Person (PMC) ] ──(OneToOne)──> [ EmployeeProfile (HRPM) ]
                                            │
                                            ├── [ LeaveRequest ]
                                            └── [ PayrollRun ]
```

---

## 2. Recruitment & Candidate ATS
- **JobOpening**: Published vacancy parameters.
- **Candidate**: Applicant details and stage tracking (applied, interviewing, offered, hired).
- **Interview**: Candidate screening panel notes and scores logs.

---

## 3. Leave Calendars
- **LeaveRequest**: Request dates and approval statuses (`pending`, `approved`, `rejected`).
- **LeaveBalance**: Dynamic allowed and remaining days counters tracking sick or annual leaves.

---

## 4. REST APIs
Endpoints are mounted under `/hr/api/v1/`:
- `GET/POST /hr/employees/`: Manage directories.
- `GET/POST /hr/leave/`: Manage time off requests.
- `GET/POST /hr/payroll/`: Process payroll periods runs.
