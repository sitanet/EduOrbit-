# Appendix J — Release History & Versioning (`docs/release_history.md`)

## Release History Log

### Version 1.1.0-RELEASE (July 27, 2026)
- **Module Lock Status**: `FROZEN & LOCKED`
- **Key Enhancements**:
  - 12-state `EMPLOYEE_LIFECYCLE_STATUS` master enum.
  - 7-tier organizational structure (`Company` -> `Campus` -> `Division` -> `Directorate` -> `Department` -> `Unit` -> `Team`).
  - Decoupled `JobPosition` headcount vacancy engine.
  - 8-Step Enterprise Onboarding Wizard (`Wizard V1`) at `/hr/admin/onboarding/wizard/`.
  - 5-second wizard draft auto-save (`OnboardingDraft`).
  - Pluggable `KYCProvider` Strategy pattern (**Dojah API** + zero-config **Sandbox Mode**).
  - AES-256 field encryption for NIN, BVN, RSA PIN, and Tax TIN with RBAC masking (`********1234`).
  - Statutory Nigerian PAYE tax (CRA progressive bands), 8% Pension, 2.5% NHF, and PDF payslip engine.
  - Double-entry General Ledger accounting posting ($	ext{Debits} = 	ext{Credits} = 	ext{₦1,100,000.00}$).
  - `ApprovalWorkflow` dynamic approval workflow designer model.

### Version 1.0.0 (Legacy Base)
- Initial core employee roster and basic leave tracking.
