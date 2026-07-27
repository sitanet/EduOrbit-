# EduOrbit HRMS v1.1.0 — Production Release Checklist (`hr_production_checklist.md`)

> **Release Version**: `v1.1.0-RELEASE`  
> **Status**: `PASSED & APPROVED FOR PRODUCTION`

---

## 1. System Readiness Verification Checklist

- [x] **`DEBUG = False`**: Verified in production Django settings.
- [x] **Database Integrity**: All Django migrations applied (`0001` through `0009_approvalworkflow`).
- [x] **System Integrity Check**: `python manage.py check` executed with 0 errors and 0 warnings.
- [x] **Unit & Integration Test Suite**: 100% test pass rate across all 6 phase test batteries.
- [x] **Real Browser Route Crawl**: All 26 Web Routes return HTTP 200 OK.
- [x] **Field Encryption**: AES-256 Fernet key active for NIN, BVN, RSA PIN, and Tax TIN. Masking (`********1234`) enforced.
- [x] **Dojah KYC Fallback**: Pluggable `KYCProvider` Strategy pattern routes to live Dojah API when keys are configured, or zero-config Sandbox Mode otherwise.
- [x] **Double-Entry Ledger Integrity**: Payroll GL postings balance perfectly ($\text{Debits} = \text{Credits}$).
- [x] **SLA Benchmarks**: Global search <300ms, Payroll run <60s, Dashboard load <2.0s.
- [x] **Static Assets**: Compiled and collected via `collectstatic`.
