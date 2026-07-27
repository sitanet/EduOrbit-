# Appendix C — Role-Based Access Control Matrix (`docs/appendices/rbac_matrix.md`)

| Permission Flag / Capability | `hr.admin` | `payroll.admin` | `dept.manager` | `staff.member` | `finance.officer` |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **View Staff Directory** | `YES` | `YES` | Direct Reports | Self Only | `NO` |
| **Launch Onboarding Wizard** | `YES` | `NO` | `NO` | `NO` | `NO` |
| **Verify Dojah NIN / BVN** | `YES` | `YES` | `NO` | `NO` | `NO` |
| **View Unmasked PII Data** | `YES` | `YES` | `NO` | Self Only | `NO` |
| **Execute Payroll Calculation**| `NO` | `YES` | `NO` | `NO` | `NO` |
| **Post Journal Entries to GL** | `NO` | `YES` | `NO` | `NO` | `YES` |
| **Approve Leave Applications** | `YES (L2)`| `NO` | `YES (L1)` | `NO` | `NO` |
| **Clock In / Out Terminal** | `YES` | `YES` | `YES` | `YES` | `YES` |
