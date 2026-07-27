# Appendix G — Transactional Outbox Domain Event Schemas (`docs/appendices/domain_events.md`)

- `employee.created`: Triggered when an employee profile is created.
- `employee.nin_verified`: Triggered upon successful NIN KYC verification.
- `employee.bvn_verified`: Triggered upon successful BVN KYC verification.
- `payroll.calculated`: Triggered upon monthly payroll calculation.
- `payroll.posted`: Triggered when GL journal entries post to Finance module.
