# EduOrbit HRMS v1.1.0 — Employee Self-Service Guide (`hr_employee_guide.md`)

> **Target Role**: Staff Member / Teacher (`staff.member`)  
> **Access Level**: Employee Self-Service (ESS) Workspace  
> **Portal URL**: `/hr/ess/`

---

## 1. Employee Self-Service (ESS) Overview

The ESS Workspace is the central hub for employees to register attendance, submit leave applications, download digital PDF payslips, track assigned assets, and participate in peer recognition.

### 1.1 Logging In
- **URL**: `http://127.0.0.1:8000/login/`
- **Demo Username**: `staff.member`
- **Demo Password**: `Demo@2026`
- **Landing Page**: Automatically routes to `/hr/ess/`.

---

## 2. Daily Attendance & Clock-In Terminal

- **Navigation**: Top Right Header on `/hr/ess/`.
- **Clock In Procedure**:
  1. Click the blue **⏰ Clock In / Out** terminal button.
  2. The system captures timestamp (e.g. `07:58:14 AM`).
  3. Evaluates 15-minute shift grace period (Status: `Present / On Time`).
  4. At end of shift, click the button again to register Check-Out timestamp.

---

## 3. Leave Applications & Balance Tracking

- **Navigation**: `/hr/ess/` → `My Leave` Tab.
- **Applying for Leave**:
  1. Click the purple **+ Apply for Leave** button.
  2. Select Leave Type (*Annual Leave*, *Casual Leave*, *Sick Leave*).
  3. Input Start Date (e.g. `2026-08-01`) and End Date (`2026-08-05`).
  4. Enter application reason and click **Submit Application**.
  5. Application enters the 2-tier approval workflow (Supervisor → HR Admin).

---

## 4. Digital PDF Payslips & Rewards

- **Downloading Payslips**:
  1. Click `My Payslips` Tab.
  2. Locate target period (e.g. `July 2026`).
  3. Click **Download PDF** to save official payslip document.
- **Wall of Fame Recognition**:
  1. Navigate to `/hr/rewards/`.
  2. Click **🏆 Nominate Employee** to nominate a peer for an award.
