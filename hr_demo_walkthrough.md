# EduOrbit HRMS v1.1.0 — Demo & System Walkthrough Guide (`hr_demo_walkthrough.md`)

> **Target Audience**: Product Managers, Sales Engineering, Demonstrators, Executive Stakeholders  
> **Environment**: `http://127.0.0.1:8000`

---

## 1. Executive Demo Script & Sequence

### Demo Sequence Overview (15-Minute Live Presentation)
1. **Scene 1: HR Executive Dashboard (`/hr/admin/dashboard/`)**
   - Demonstrate real-time HR KPIs, headcount metrics, and active recruitment alerts.
2. **Scene 2: Enterprise Onboarding Wizard (`/hr/admin/onboarding/wizard/`)**
   - Click `+ Add Staff Member (Enterprise Wizard)`.
   - Input NIN `12345678901` and click `⚡ Verify NIN` -> Show instant Dojah identity match card for Natasha Romanoff.
   - Input BVN `22345678901` and click `⚡ Verify BVN` -> Show BVN verification match.
   - Show 5-second auto-save draft indicator (`⚡ Saved at 14:15:32`).
3. **Scene 3: Attendance Clock-In & Grace Period Engine (`/hr/ess/`)**
   - Login as `staff.member`.
   - Click `⏰ Clock In / Out` terminal button -> Show automatic timestamp registration and shift grace period evaluation.
4. **Scene 4: Monthly Payroll Run & Statutory PAYE (`/hr/payroll/`)**
   - Login as `payroll.admin`.
   - Click `⚡ Run Monthly Payroll Calculation` for July 2026.
   - Show breakdown of Base Salary, CRA, Progressive PAYE Tax, 8% Pension, and 2.5% NHF.
   - Click `Post to Finance GL` -> Show double-entry journal balance ($\text{Debits} = \text{Credits} = \text{₦1,100,000.00}$).
5. **Scene 5: Interactive Web User Manual (`/hr/manual/`)**
   - Show live 7-Step Live Demo Simulator and Statutory Tax Calculator widget.
