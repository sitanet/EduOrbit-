# Appendix A — Enterprise Domain Glossary (`docs/glossary.md`)

- **CRA (Consolidated Relief Allowance)**: Statutory tax deduction defined under Nigerian Personal Income Tax Act (PITA) equal to MAX(₦200k/yr, 1% Gross) + 20% Gross.
- **NUBAN (Nigerian Uniform Bank Account Number)**: 10-digit bank account number standard validated via Interswitch/Dojah NUBAN API.
- **Dojah KYC**: Third-party identity verification service provider for real-time NIN and BVN validation.
- **Transactional Outbox**: Architecture pattern storing domain events in a database table inside transaction boundaries prior to Celery dispatch.
- **SaaS Tenant Isolation**: Multi-tenant database boundary enforcing isolation per educational institution.
