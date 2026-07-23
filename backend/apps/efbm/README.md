# Enterprise Finance, Fees & Billing Management (EFBM) Documentation

This document describes the structure, billing rule configurations, double-entry general ledger, parent wallets, and platform SaaS subscription details of the **efbm** app.

---

## 1. Double-Entry Accounting Architecture
All financial movements must balance. The system utilizes dedicated general ledger models:
```
[ JournalEvent ] ──> The transaction category trigger (billing, payment)
       │
       ▼
[ JournalEntry ] ──> Debit or Credit records (Receivables, Cash)
       │
       ▼
[ LedgerPosting ] ──> Immutable date post log
```
*Note: Sibling discounts and bursaries are modeled as `FinancialAid` and debit the scholarship expense account while crediting student receivables.*

---

## 2. Parent Wallets & Sibling Allocations
- **StudentWallet**: Pre-paid parent funding balances.
- **WalletTransaction**: Audited debits and credits logs.
- **PaymentAllocation**: Breaks a single bulk transaction payment down across individual outstanding invoice items.

---

## 3. Platform SaaS Subscription & Monetization
- **TenantSubscriptionInvoice**: Billed to the institutional school owner based on active licensed modules.
- **PlatformCommission**: Commission fees deducted from public marketplace gateway settlements.

---

## 4. REST APIs
Endpoints are mounted under `/efbm/api/v1/`:
- `GET/POST /efbm/invoices/`: Issue and manage invoices.
- `GET/POST /efbm/payments/`: Record settlements.
- `GET/POST /efbm/wallet/`: Manage parent wallets funding.
