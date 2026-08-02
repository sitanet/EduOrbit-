# Requirements: Accounts Payable Phase 2 - Supplier Bill Management

## Overview
Implement complete supplier bill management functionality for the EduOrbit ERP system, enabling schools to track, approve, and manage vendor invoices with full audit trails and integration with the general ledger.

## Business Context
Schools need to manage supplier bills (vendor invoices) from creation through approval and payment. This module must support multi-level approval workflows, prevent duplicate invoices, maintain complete audit trails, and automatically post journal entries to the general ledger.

## Stakeholders
- **Primary**: Finance Officers, Accounts Payable Clerks, School Administrators
- **Secondary**: CFOs, Auditors, School Principals
- **Technical**: Django Backend Developers, ERP Architects

## Functional Requirements

### FR-1: Supplier Bill Creation
**Priority**: Critical  
**Description**: Users must be able to create supplier bills with complete invoice details.

**Acceptance Criteria**:
- System validates supplier exists in the Supplier master table
- Bill number must be unique across the system
- System prevents duplicate invoice numbers for the same supplier
- Users can attach multiple file attachments (invoice PDFs, supporting documents)
- System calculates total from subtotal, tax, and other charges
- Due date must be after or equal to issue date
- System auto-generates bill number if not provided
- All fields respect multi-tenant isolation

**Business Rules**:
- A supplier cannot have duplicate bill numbers
- Bill amounts must be positive and greater than zero
- Due date validation: cannot be in the past
- Attachments are optional but recommended for audit compliance

### FR-2: Supplier Bill Update
**Priority**: Critical  
**Description**: Users must be able to edit draft supplier bills before submission.

**Acceptance Criteria**:
- Only bills in 'draft' status can be edited
- All fields can be modified except bill ID and creation metadata
- System prevents editing of submitted, approved, or paid bills
- Audit log captures all changes with before/after values
- Changes preserve multi-tenant isolation

**Business Rules**:
- Status transitions: Only 'draft' bills are editable
- Supplier cannot be changed once bill is submitted
- Bill number can be edited only in draft status

### FR-3: Supplier Bill Submission for Approval
**Priority**: Critical  
**Description**: Users must be able to submit draft bills for approval workflow.

**Acceptance Criteria**:
- System transitions bill from 'draft' to 'submitted' status
- System identifies applicable approval matrix based on amount and category
- System initializes approval workflow with all required approval levels
- First approver receives notification (email/system notification)
- Submission creates audit trail entry
- Submitted bills are locked from editing

**Business Rules**:
- Bills cannot be submitted without complete required fields
- Approval matrix selection based on bill amount and category
- Sequential approval: Level 2 cannot approve until Level 1 completes

### FR-4: Multi-Level Bill Approval
**Priority**: Critical  
**Description**: Authorized approvers must be able to approve bills at their assigned level.

**Acceptance Criteria**:
- System validates approver has authority for current approval level
- Approver can view complete bill details and attachments
- Approver can add approval comments
- System progresses to next approval level automatically
- Final approval transitions bill to 'approved' status
- System creates journal entries upon final approval
- All approvals are logged in audit trail

**Business Rules**:
- Approvers cannot approve their own submitted bills
- Approval must follow sequence: Level 1 → Level 2 → Level 3
- Amount-based routing: Bills over threshold require additional approval
- Delegation: Approvers can delegate to authorized deputies if enabled

### FR-5: Bill Rejection
**Priority**: High  
**Description**: Approvers must be able to reject bills with rejection reason.

**Acceptance Criteria**:
- Approver provides mandatory rejection reason
- System transitions bill to 'rejected' status
- Bill returns to draft status for corrections
- Rejection notification sent to bill creator
- Rejection reason recorded in audit log
- Rejected bills can be corrected and resubmitted

**Business Rules**:
- Rejection at any level returns bill to draft
- Rejection clears all pending approvals
- Resubmission initiates fresh approval workflow

### FR-6: Bill Cancellation
**Priority**: High  
**Description**: Authorized users must be able to cancel bills before payment.

**Acceptance Criteria**:
- Only unpaid bills can be cancelled
- System transitions bill to 'cancelled' status
- Cancellation requires reason and authorization
- Cancelled bills cannot be paid or edited
- Cancellation creates audit trail entry
- If approved bill is cancelled, journal entries are reversed

**Business Rules**:
- Paid or partially paid bills cannot be cancelled
- Cancellation reverses any posted journal entries
- Cancelled bills remain in system for audit purposes

### FR-7: Supplier Ledger Update
**Priority**: Critical  
**Description**: System must maintain accurate supplier ledger for all transactions.

**Acceptance Criteria**:
- Bill approval creates ledger entry (debit to supplier account)
- Payment creates ledger entry (credit to supplier account)
- System maintains running balance for each supplier
- Ledger entries are immutable (no updates/deletes)
- Each entry links to source transaction (bill/payment/note)
- Ledger respects multi-tenant isolation

**Business Rules**:
- Ledger entries created atomically with parent transaction
- Balance calculation: running total of all debits minus credits
- Ledger entries must balance with SupplierBalance table

### FR-8: Automatic Journal Posting
**Priority**: Critical  
**Description**: System must automatically post balanced journal entries to general ledger.

**Acceptance Criteria**:
- Bill approval creates journal entries:
  - Debit: Expense Account (based on category)
  - Credit: Accounts Payable
- Journal entries are balanced (total debits = total credits)
- System uses AutomaticAccountingIntegrationService
- Journal reference links back to supplier bill ID
- Journal posting is atomic with bill approval

**Business Rules**:
- All journal entries must balance
- Account mapping: Bill category → GL expense account
- Failed journal posting rolls back bill approval
- Journal entries immutable after posting

### FR-9: Audit Trail
**Priority**: Critical  
**Description**: System must maintain complete audit trail for all bill operations.

**Acceptance Criteria**:
- Every financial action creates SupplierBillAudit entry
- Audit captures: user, timestamp, action, before/after state
- Audit trail is immutable (no updates/deletes)
- Audit accessible by authorized users only
- Audit supports compliance and forensic analysis

**Business Rules**:
- Audit creation is mandatory for all state changes
- Audit entries survive even if parent bill is deleted
- Audit trail respects data privacy regulations

### FR-10: Duplicate Invoice Prevention
**Priority**: High  
**Description**: System must prevent duplicate supplier invoices.

**Acceptance Criteria**:
- System validates bill number uniqueness per supplier
- Duplicate detection before saving
- Clear error message for duplicate attempts
- Case-insensitive duplicate checking
- Support for manual override with authorization

**Business Rules**:
- Duplicate check: Same supplier + same bill number
- Override requires supervisor authorization
- Legitimate duplicates (e.g., credit notes) use different number scheme

## Non-Functional Requirements

### NFR-1: Performance
- Bill creation/update: < 500ms response time
- Approval workflow initialization: < 1 second
- Ledger queries: < 2 seconds for 10,000 records
- Bulk operations: Handle 1,000 bills per batch

### NFR-2: Security
- Role-based access control (RBAC) for all operations
- Multi-tenant isolation: No cross-tenant data access
- Audit trail for security compliance
- Secure file upload with virus scanning
- Input validation and sanitization

### NFR-3: Data Integrity
- All financial operations wrapped in database transactions
- Foreign key constraints enforced
- No orphaned records
- Atomic operations: all-or-nothing updates
- Data consistency checks on save

### NFR-4: Scalability
- Support 10,000+ active bills per school
- Support 1,000+ suppliers per school
- Horizontal scaling capability
- Database query optimization (indexes, select_related)

### NFR-5: Maintainability
- Follow Django best practices
- Service-oriented architecture
- Comprehensive inline documentation
- Unit test coverage > 80%
- Integration test for critical paths

### NFR-6: Usability
- Clear error messages
- Intuitive form validation
- Responsive UI (mobile-friendly)
- Accessibility compliance (WCAG 2.1 Level AA)

## Out of Scope (Phase 2)
The following features are explicitly out of scope for Phase 2:
- Payment processing (Phase 3)
- Credit notes (Phase 3)
- Debit notes (Phase 3)
- Payment batches (Phase 3)
- Withholding tax calculations (Phase 3)
- Supplier statements (Phase 3)
- Vendor aging reports (Phase 4)
- Payment scheduling (Phase 4)
- Recurring bills (Phase 4)

## Success Metrics
- All FR acceptance criteria met and verified
- Zero duplicate invoice incidents
- 100% audit trail coverage
- All tests passing (unit + integration)
- Code review approval from senior architect
- Performance benchmarks met
- Django `manage.py check` passes with no errors

## Assumptions
- Supplier master data already exists (from Task 4)
- AutomaticAccountingIntegrationService is functional
- Django 4.2+ environment
- PostgreSQL database
- Multi-tenant infrastructure is operational
- User authentication system is in place

## Dependencies
- Backend: Django 4.2+, Python 3.10+
- Database: PostgreSQL 14+
- Existing models: Supplier, TenantBaseModel, SupplierBill, SupplierLedger, ApprovalMatrix, ApprovalLevel, BillApproval, SupplierBillAudit
- Existing services: AutomaticAccountingIntegrationService
- Frontend: HTMX, Tailwind CSS (for templates)

## Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Approval workflow complexity | High | Medium | Design simple, testable workflow logic; comprehensive testing |
| Journal posting failures | High | Low | Wrap in transactions; implement rollback logic |
| Performance with large datasets | Medium | Medium | Add database indexes; use select_related/prefetch_related |
| Duplicate invoice edge cases | Medium | Low | Comprehensive validation; manual override capability |
| Multi-tenant data leakage | High | Low | Enforce tenant filter in all queries; security audit |

## Compliance Requirements
- IFRS/GAAP accounting standards
- Audit trail for financial regulations
- Data privacy (GDPR/CCPA where applicable)
- Access control and authorization
- Data retention policies

## Glossary
- **Supplier Bill**: Vendor invoice awaiting approval and payment
- **Approval Matrix**: Configuration defining approval workflow based on amount/category
- **Approval Level**: Single step in multi-level approval workflow
- **Supplier Ledger**: Transaction history for individual supplier
- **Journal Entry**: Double-entry accounting record in general ledger
- **Audit Trail**: Immutable log of all financial actions
- **Multi-tenant**: Architecture supporting multiple schools in single database
