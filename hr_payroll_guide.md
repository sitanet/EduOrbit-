# EduOrbit HRMS v1.1.0 — Payroll Specialist & Finance Guide (`hr_payroll_guide.md`)

> **Target Role**: Payroll Specialist / Finance Officer (`payroll.admin`, `finance.officer`)  
> **Access Level**: Full Payroll Calculation & GL Postings Control  
> **Console URL**: `/hr/payroll/`

---

## 1. Payroll Console Overview

- **Navigation**: `/hr/payroll/`
- **Key Capabilities**: Monthly payroll generation, statutory PAYE progressive tax computation, 8% Pension deduction, 2.5% NHF deduction, PDF payslip batch generation, and double-entry General Ledger posting.

---

## 2. Generating Monthly Payroll

1. **Select Payroll Period**: Choose month/year (e.g. `July 2026`).
2. **Execute Payroll Run**: Click **⚡ Run Monthly Payroll Calculation**.
3. **Statutory Computations Executed Automatically**:
   - **Gross Salary**: Base + Housing + Transport + Allowances.
   - **Consolidated Relief Allowance (CRA)**: $\max(\text{₦200,000 / 12}, 1\% \times \text{Gross}) + (20\% \times \text{Gross})$.
   - **Pension Contribution**: $8\% \times (\text{Basic} + \text{Housing} + \text{Transport})$.
   - **National Housing Fund (NHF)**: $2.5\% \times \text{Basic Salary}$.
   - **Progressive PAYE Tax Bands**: Applied to Chargeable Income ($7\%, 11\%, 15\%, 19\%, 21\%, 24\%$).

---

## 3. General Ledger (GL) Postings & Double-Entry Accounting

- **Navigation**: `/hr/finance/postings/`
- **Posting Double-Entry Journals**:
  1. Review calculated payroll run totals (Total Salaries, Total PAYE Tax, Total Pension).
  2. Click **Post to Finance GL**.
  3. The system generates balanced double-entry journal entries:
     - **Debit**: Salaries & Wages Expense Account (`5001-SALARIES`).
     - **Credit**: Bank Cash Account (`1001-GTBANK-MAIN`), PAYE Tax Liability (`2001-PAYE-TAX`), Pension Liability (`2002-PENSION-LTD`).
  4. **Balance Condition**: Verifies $\text{Total Debits} = \text{Total Credits} = \text{₦1,100,000.00}$.
