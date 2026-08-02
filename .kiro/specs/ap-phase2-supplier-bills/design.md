# Technical Design: Accounts Payable Phase 2 - Supplier Bill Management

## Architecture Overview

This design implements supplier bill management following Django best practices, service-oriented architecture, and the existing EduOrbit ERP patterns. The implementation consists of:

1. **Service Layer** (`backend/apps/efbm/services/payables.py`) - Business logic and orchestration
2. **View Layer** (`backend/apps/efbm/views_web.py`) - Web request handling
3. **Template Layer** (`backend/templates/efbm/payables/`) - User interface
4. **URL Configuration** (`backend/apps/efbm/urls.py`) - Route mapping
5. **Test Suite** (`backend/apps/efbm/tests/test_supplier_bills.py`) - Quality assurance

## Design Principles

- **Single Responsibility**: Each service method has one clear purpose
- **Transaction Atomicity**: All financial operations wrapped in `transaction.atomic()`
- **Fail-Safe**: Rollback on any error; never leave partial state
- **Multi-Tenant Isolation**: Every query filtered by tenant
- **Audit Trail**: Every state change logged to SupplierBillAudit
- **Immutable Ledger**: Ledger entries never updated, only created
- **Balanced Journals**: All GL postings must balance (debits = credits)

## Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Web Layer (Views)                      │
│  SupplierBillCreateView │ SupplierBillUpdateView │ etc.   │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                   Service Layer (Business Logic)            │
│              AccountsPayableService                         │
│  create_supplier_bill() │ approve_supplier_bill() │ etc.  │
└────────┬────────────────────────────┬───────────────────────┘
         │                            │
         ▼                            ▼
┌────────────────────┐    ┌──────────────────────────────────┐
│   Model Layer      │    │  Integration Services            │
│  SupplierBill      │    │  AutomaticAccountingIntegration  │
│  SupplierLedger    │    │  Service                         │
│  BillApproval      │    └──────────────────────────────────┘
│  SupplierBillAudit │
└────────────────────┘
```


## Service Layer Design

### Class: AccountsPayableService

Location: `backend/apps/efbm/services/payables.py`

#### Method: create_supplier_bill()

**Purpose**: Create a new supplier bill with validation and audit trail

**Signature**:
```python
@staticmethod
def create_supplier_bill(
    tenant,
    supplier_id: str,
    bill_number: str,
    issue_date: date,
    due_date: date,
    subtotal: Decimal,
    tax_amount: Decimal,
    total_amount: Decimal,
    category: str,
    description: str = "",
    attachments: list = None,
    created_by = None
) -> SupplierBill
```

**Algorithm**:
1. Begin transaction
2. Validate supplier exists and belongs to tenant
3. Check for duplicate bill number for this supplier
4. Validate due_date >= issue_date
5. Validate amounts are positive
6. Create SupplierBill with status='draft'
7. Create initial audit log entry
8. Commit transaction
9. Return created bill

**Error Handling**:
- Supplier not found → raise ValueError
- Duplicate bill number → raise ValidationError
- Invalid dates → raise ValidationError
- Transaction failure → rollback and raise


#### Method: update_supplier_bill()

**Purpose**: Update draft supplier bill before submission

**Signature**:
```python
@staticmethod
def update_supplier_bill(
    bill_id: str,
    user,
    **update_fields
) -> SupplierBill
```

**Algorithm**:
1. Begin transaction
2. Fetch bill with tenant filter
3. Validate bill status is 'draft'
4. Capture before state for audit
5. Update allowed fields
6. Validate updated data
7. Save bill
8. Create audit log with before/after
9. Commit transaction
10. Return updated bill

**Validation Rules**:
- Only draft bills can be edited
- Supplier cannot be changed after creation
- Due date >= issue date
- Amounts must be positive

**Error Handling**:
- Bill not found → raise DoesNotExist
- Status not draft → raise PermissionError
- Validation failure → raise ValidationError


#### Method: submit_supplier_bill()

**Purpose**: Submit draft bill for approval workflow

**Signature**:
```python
@staticmethod
def submit_supplier_bill(
    bill_id: str,
    user
) -> SupplierBill
```

**Algorithm**:
1. Begin transaction
2. Fetch bill with tenant filter
3. Validate bill status is 'draft'
4. Validate all required fields present
5. Find applicable ApprovalMatrix (by amount and category)
6. Create BillApproval records for each level
7. Update bill status to 'submitted'
8. Create audit log entry
9. Send notification to first approver
10. Commit transaction
11. Return updated bill

**Approval Matrix Selection**:
- Query ApprovalMatrix where:
  - is_active = True
  - min_amount <= bill.total_amount
  - max_amount >= bill.total_amount (or max_amount is NULL)
  - category matches or category is blank (matches all)
- Order by specificity (category match > amount range)
- Select first matching matrix

**Error Handling**:
- Bill not draft → raise PermissionError
- No approval matrix found → raise ConfigurationError
- Missing required fields → raise ValidationError


#### Method: approve_supplier_bill()

**Purpose**: Approve bill at current approval level

**Signature**:
```python
@staticmethod
def approve_supplier_bill(
    bill_id: str,
    approval_level_id: str,
    approver,
    comments: str = ""
) -> SupplierBill
```

**Algorithm**:
1. Begin transaction
2. Fetch bill and approval level
3. Validate bill status is 'submitted' or 'pending'
4. Validate approver has authority for this level
5. Validate previous levels are approved (if sequential)
6. Update BillApproval status to 'approved'
7. Set approval_date and comments
8. Check if all required levels approved
9. If all approved:
   - Update bill status to 'approved'
   - Create supplier ledger entry (debit)
   - Post journal entries (DR Expense, CR Accounts Payable)
   - Update SupplierBalance
10. Else:
    - Notify next approver
11. Create audit log entry
12. Commit transaction
13. Return updated bill

**Journal Entry Pattern**:
```
DR  Expense Account (category-based)     Amount
    CR  Accounts Payable                 Amount
```

**Error Handling**:
- Approver not authorized → raise PermissionError
- Previous level not approved → raise WorkflowError
- Journal posting failure → rollback entire transaction


#### Method: reject_supplier_bill()

**Purpose**: Reject bill with reason and return to draft

**Signature**:
```python
@staticmethod
def reject_supplier_bill(
    bill_id: str,
    approval_level_id: str,
    approver,
    rejection_reason: str
) -> SupplierBill
```

**Algorithm**:
1. Begin transaction
2. Fetch bill and approval level
3. Validate bill is in approval workflow
4. Validate rejection_reason is provided
5. Update BillApproval status to 'rejected'
6. Set rejection comments
7. Update bill status to 'draft'
8. Clear all other pending approvals
9. Create audit log entry
10. Notify bill creator
11. Commit transaction
12. Return updated bill

**Business Logic**:
- Rejection at any level returns bill to draft
- All pending approvals are cleared
- Bill creator must fix and resubmit
- New submission starts fresh approval workflow

#### Method: cancel_supplier_bill()

**Purpose**: Cancel bill before payment

**Signature**:
```python
@staticmethod
def cancel_supplier_bill(
    bill_id: str,
    user,
    cancellation_reason: str
) -> SupplierBill
```

**Algorithm**:
1. Begin transaction
2. Fetch bill with tenant filter
3. Validate bill not paid or partially paid
4. Validate cancellation_reason provided
5. If bill is approved:
   - Reverse supplier ledger entry (credit)
   - Reverse journal entries
   - Update SupplierBalance
6. Update bill status to 'cancelled'
7. Create audit log entry
8. Commit transaction
9. Return updated bill

**Journal Reversal Pattern**:
```
DR  Accounts Payable                 Amount
    CR  Expense Account               Amount
```


### Helper Methods

#### _create_audit_log()

**Purpose**: Create immutable audit trail entry

**Signature**:
```python
@staticmethod
def _create_audit_log(
    bill: SupplierBill,
    action: str,
    user,
    before_state: dict = None,
    after_state: dict = None,
    notes: str = ""
)
```

**Implementation**:
- Create SupplierBillAudit record
- Capture: bill_id, action, user, timestamp, before/after state, notes
- Return created audit entry

#### _update_supplier_ledger()

**Purpose**: Create supplier ledger entry for bill approval

**Signature**:
```python
@staticmethod
def _update_supplier_ledger(
    supplier: Supplier,
    bill: SupplierBill,
    transaction_type: str,
    amount: Decimal
)
```

**Implementation**:
1. Get current supplier balance (or 0 if first transaction)
2. Calculate new balance based on transaction type:
   - 'bill_approval': balance += amount (debit)
   - 'bill_cancellation': balance -= amount (credit)
3. Create SupplierLedger entry with running balance
4. Update or create SupplierBalance record

#### _initiate_approval_workflow()

**Purpose**: Initialize approval workflow for submitted bill

**Signature**:
```python
@staticmethod
def _initiate_approval_workflow(
    bill: SupplierBill,
    approval_matrix: ApprovalMatrix
)
```

**Implementation**:
1. Fetch all ApprovalLevels for matrix (ordered by level_order)
2. For each level:
   - Create BillApproval record
   - Set approver from level configuration
   - Status = 'pending'
3. Return list of created approvals


## View Layer Design

### Class-Based Views

All views extend Django's `View` class and follow existing EduOrbit patterns.

#### SupplierBillListView

**URL**: `/efbm/payables/bills/`  
**Methods**: GET  
**Purpose**: Display paginated list of supplier bills with filters

**GET Logic**:
1. Check authentication
2. Get tenant from request
3. Apply filters from query params:
   - status (draft, submitted, approved, paid, cancelled)
   - supplier_id
   - date_range (issue_date)
   - category
4. Query SupplierBill with tenant filter
5. Use select_related('supplier') for optimization
6. Paginate results (50 per page)
7. Render template with context

**Template Context**:
```python
{
    'bills': paginated_bills,
    'suppliers': Supplier.objects.filter(tenant=tenant),
    'status_choices': SupplierBill.STATUS_CHOICES,
    'filter_params': {status, supplier_id, date_range, category}
}
```

#### SupplierBillCreateView

**URL**: `/efbm/payables/bills/create/`  
**Methods**: GET, POST  
**Purpose**: Create new supplier bill

**GET Logic**:
1. Check authentication and permissions
2. Get tenant and suppliers
3. Render form with empty fields

**POST Logic**:
1. Validate form data
2. Call AccountsPayableService.create_supplier_bill()
3. Handle success: redirect to detail view with success message
4. Handle errors: re-render form with error messages

**Form Fields**:
- supplier (dropdown, required)
- bill_number (text, required)
- issue_date (date picker, default=today)
- due_date (date picker, required)
- category (dropdown, required)
- subtotal (decimal, required)
- tax_amount (decimal, default=0)
- total_amount (decimal, calculated)
- description (textarea, optional)
- attachments (file upload, multiple, optional)


#### SupplierBillDetailView

**URL**: `/efbm/payables/bills/<uuid:bill_id>/`  
**Methods**: GET, POST  
**Purpose**: View bill details and perform actions

**GET Logic**:
1. Check authentication
2. Fetch bill with tenant filter
3. Use select_related for related objects
4. Fetch audit trail
5. Fetch approval workflow status
6. Render detail template

**POST Actions**:
- `submit`: Call submit_supplier_bill()
- `approve`: Call approve_supplier_bill()
- `reject`: Call reject_supplier_bill()
- `cancel`: Call cancel_supplier_bill()

**Template Context**:
```python
{
    'bill': bill_object,
    'audit_trail': SupplierBillAudit.objects.filter(bill=bill),
    'approvals': BillApproval.objects.filter(bill=bill).order_by('approval_level__level_order'),
    'can_edit': bill.status == 'draft',
    'can_submit': bill.status == 'draft',
    'can_approve': user has approval permission,
    'can_cancel': bill.status not in ['paid', 'cancelled']
}
```

#### SupplierBillUpdateView

**URL**: `/efbm/payables/bills/<uuid:bill_id>/edit/`  
**Methods**: GET, POST  
**Purpose**: Edit draft supplier bill

**GET Logic**:
1. Check authentication
2. Fetch bill with tenant filter
3. Verify status is 'draft'
4. Render form with pre-filled data

**POST Logic**:
1. Validate form data
2. Call AccountsPayableService.update_supplier_bill()
3. Handle success: redirect to detail view
4. Handle errors: re-render form with errors

**Validation**:
- Only draft bills can be edited
- Supplier field is read-only (displayed but not editable)


## Template Design

All templates use Tailwind CSS and follow EduOrbit design patterns.

### supplier_bills.html (List View)

**Structure**:
```html
- Header: "Supplier Bills" + Create New button
- Filters bar:
  - Status dropdown (All, Draft, Submitted, Approved, Paid, Cancelled)
  - Supplier dropdown
  - Date range picker
  - Category dropdown
  - Search button
- Table:
  - Columns: Bill #, Supplier, Issue Date, Due Date, Amount, Status, Actions
  - Status badges: color-coded by status
  - Actions: View, Edit (if draft), Delete (if draft)
- Pagination controls
```

**Status Badge Colors**:
- Draft: gray
- Submitted: blue
- Approved: green
- Paid: green
- Cancelled: red

**Features**:
- Responsive: stack on mobile
- Sortable columns
- Row click → detail view
- HTMX for filter updates (no page reload)

### supplier_bill_form.html (Create/Edit)

**Structure**:
```html
- Form header: "Create Supplier Bill" or "Edit Supplier Bill"
- Form sections:
  1. Supplier Information
     - Supplier dropdown (searchable)
     - Bill number input
  2. Dates
     - Issue date (date picker)
     - Due date (date picker)
  3. Financial Details
     - Category dropdown
     - Subtotal input
     - Tax amount input
     - Total (auto-calculated, read-only)
  4. Description
     - Textarea
  5. Attachments
     - File upload (drag & drop)
- Form actions:
  - Save as Draft
  - Cancel (return to list)
```

**JavaScript**:
- Auto-calculate total: subtotal + tax
- Date validation: due_date >= issue_date
- Client-side validation before submit
- File upload preview


### supplier_bill_detail.html (Detail View)

**Structure**:
```html
- Header: Bill number + status badge
- Action buttons (contextual based on status):
  - Edit (if draft)
  - Submit for Approval (if draft)
  - Approve (if user is next approver)
  - Reject (if user is next approver)
  - Cancel (if not paid)
- Bill Information Card:
  - Supplier details
  - Bill number, dates
  - Amounts (subtotal, tax, total)
  - Category, description
- Approval Workflow Card (if submitted/approved):
  - Approval matrix name
  - List of approval levels with status
  - Approver names, dates, comments
  - Visual progress indicator
- Attachments Section:
  - List of uploaded files with download links
- Audit Trail Card:
  - Timeline of all actions
  - User, timestamp, action, notes
  - Collapsible for long histories
```

**Modal Dialogs**:
- Approve: Approval comments input
- Reject: Rejection reason input (required)
- Cancel: Cancellation reason input (required)

**HTMX Features**:
- Inline approval/rejection without page reload
- Real-time approval status updates
- Optimistic UI updates with rollback on error

## URL Configuration

Location: `backend/apps/efbm/urls.py`

**New Routes**:
```python
# Supplier Bill Management
path('payables/bills/', SupplierBillListView.as_view(), name='supplier_bills_list'),
path('payables/bills/create/', SupplierBillCreateView.as_view(), name='supplier_bill_create'),
path('payables/bills/<uuid:bill_id>/', SupplierBillDetailView.as_view(), name='supplier_bill_detail'),
path('payables/bills/<uuid:bill_id>/edit/', SupplierBillUpdateView.as_view(), name='supplier_bill_edit'),
```

**Existing Routes** (already defined, will be enhanced):
```python
path('payables/', PayablesDashboardWebView.as_view(), name='payables_dashboard_web'),
```


## Database Design

All models already exist from Task 4. This section documents how they're used.

### Models Used

#### SupplierBill (Primary Model)
```python
Fields:
- supplier_name: CharField(150)
- bill_number: CharField(100, unique=True)
- issue_date: DateField
- due_date: DateField
- amount: DecimalField (legacy, will use total_amount)
- paid_amount: DecimalField
- status: CharField (pending, approved, partial, paid, cancelled)
- category: CharField(100)

Additional Fields Needed (will add via migration):
- supplier: ForeignKey(Supplier) [replace supplier_name]
- subtotal: DecimalField
- tax_amount: DecimalField
- total_amount: DecimalField [replaces amount]
- description: TextField
- submitted_at: DateTimeField(null=True)
- approved_at: DateTimeField(null=True)
```

**Status Workflow**:
```
draft → submitted → approved → partial → paid
  ↓                    ↓
cancelled          cancelled
```

#### SupplierLedger
```python
Fields:
- supplier: ForeignKey(Supplier)
- transaction_date: DateField
- description: CharField(255)
- reference_number: CharField(100)
- debit_amount: DecimalField
- credit_amount: DecimalField
- balance_after: DecimalField
- bill: ForeignKey(SupplierBill, null=True)
- payment: ForeignKey(SupplierPayment, null=True)
```

**Usage**: Track every transaction affecting supplier balance

#### BillApproval
```python
Fields:
- bill: ForeignKey(SupplierBill)
- approval_level: ForeignKey(ApprovalLevel)
- approver: ForeignKey(Person)
- status: CharField (pending, approved, rejected, delegated)
- approval_date: DateTimeField(null=True)
- comments: TextField
- delegated_to: ForeignKey(Person, null=True)
```

**Usage**: Track approval workflow progress

#### SupplierBillAudit (New Model - Need to Add)
```python
class SupplierBillAudit(TenantBaseModel):
    bill = models.ForeignKey(SupplierBill, on_delete=models.CASCADE)
    action = models.CharField(max_length=50)  # created, updated, submitted, approved, rejected, cancelled
    user = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    before_state = models.JSONField(null=True, blank=True)
    after_state = models.JSONField(null=True, blank=True)
    notes = models.TextField(blank=True)
```


## Integration Points

### AutomaticAccountingIntegrationService

**Location**: `backend/apps/efbm/services/integration.py`

**Method to Use**: `_create_balanced_journal()`

**Purpose**: Post balanced journal entries to general ledger

**Usage Pattern**:
```python
from backend.apps.efbm.services.integration import AutomaticAccountingIntegrationService

# For bill approval
AutomaticAccountingIntegrationService._create_balanced_journal(
    tenant=tenant,
    event_type='supplier_bill_approval',
    description=f'Supplier Bill {bill.bill_number} Approved',
    entries=[
        {
            'account_name': 'Operating Expenses',  # Based on category
            'amount': bill.total_amount,
            'entry_type': 'debit'
        },
        {
            'account_name': 'Accounts Payable',
            'amount': bill.total_amount,
            'entry_type': 'credit'
        }
    ],
    reference_id=str(bill.id)
)
```

**Category to GL Account Mapping**:
```python
CATEGORY_ACCOUNT_MAP = {
    'General Supplies': 'Operating Expenses',
    'IT Hardware': 'Equipment Purchases',
    'Professional Services': 'Professional Fees',
    'Utilities': 'Utilities Expense',
    'Maintenance': 'Maintenance Expense',
    # Default fallback
    'default': 'Operating Expenses'
}
```

### Notification Service (Future Phase)

**Purpose**: Send email/system notifications for:
- Bill submitted → notify first approver
- Bill approved → notify next approver (if exists) or bill creator
- Bill rejected → notify bill creator
- Bill cancelled → notify relevant parties

**Placeholder**: Use Django's logging for now, implement notifications in Phase 3


## Test Strategy

### Test File Structure

Location: `backend/apps/efbm/tests/test_supplier_bills.py`

### Test Classes

#### TestSupplierBillCreation
- test_create_valid_bill
- test_create_duplicate_bill_number
- test_create_with_invalid_supplier
- test_create_with_invalid_dates
- test_create_with_negative_amounts
- test_create_audit_trail_created

#### TestSupplierBillUpdate
- test_update_draft_bill
- test_update_submitted_bill_fails
- test_update_approved_bill_fails
- test_update_audit_trail_created

#### TestSupplierBillSubmission
- test_submit_draft_bill
- test_submit_non_draft_fails
- test_submit_creates_approval_workflow
- test_submit_audit_trail_created

#### TestSupplierBillApproval
- test_approve_single_level
- test_approve_multi_level
- test_approve_creates_ledger_entry
- test_approve_posts_journal_entries
- test_approve_updates_supplier_balance
- test_approve_without_authority_fails
- test_approve_out_of_sequence_fails

#### TestSupplierBillRejection
- test_reject_submitted_bill
- test_reject_returns_to_draft
- test_reject_clears_approvals
- test_reject_audit_trail_created

#### TestSupplierBillCancellation
- test_cancel_approved_bill
- test_cancel_reverses_ledger
- test_cancel_reverses_journals
- test_cancel_paid_bill_fails

#### TestSupplierLedger
- test_ledger_balance_calculation
- test_ledger_immutability
- test_ledger_multi_tenant_isolation

### Test Data Fixtures

**Setup in setUp() method**:
```python
def setUp(self):
    # Create tenant
    self.tenant = Tenant.objects.create(name='Test School')
    
    # Create supplier
    self.supplier = Supplier.objects.create(
        tenant=self.tenant,
        name='Test Supplier',
        email='supplier@test.com'
    )
    
    # Create approval matrix
    self.matrix = ApprovalMatrix.objects.create(
        tenant=self.tenant,
        name='Standard Approval',
        min_amount=0,
        max_amount=None,
        is_active=True
    )
    
    # Create approval levels
    self.level1 = ApprovalLevel.objects.create(
        approval_matrix=self.matrix,
        level_order=1,
        approver_role='Finance Officer'
    )
```


## Error Handling Strategy

### Exception Hierarchy

```python
class SupplierBillError(Exception):
    """Base exception for supplier bill operations"""
    pass

class BillValidationError(SupplierBillError):
    """Raised when bill data validation fails"""
    pass

class BillWorkflowError(SupplierBillError):
    """Raised when bill workflow state is invalid"""
    pass

class BillPermissionError(SupplierBillError):
    """Raised when user lacks permission for action"""
    pass

class DuplicateBillError(BillValidationError):
    """Raised when duplicate bill number detected"""
    pass
```

### Error Handling in Views

**Pattern**:
```python
def post(self, request):
    try:
        bill = AccountsPayableService.create_supplier_bill(...)
        messages.success(request, 'Supplier bill created successfully')
        return redirect('supplier_bill_detail', bill_id=bill.id)
    except DuplicateBillError as e:
        messages.error(request, f'Duplicate bill: {str(e)}')
        return render(request, 'form.html', context)
    except BillValidationError as e:
        messages.error(request, f'Validation error: {str(e)}')
        return render(request, 'form.html', context)
    except Exception as e:
        logger.exception('Unexpected error creating bill')
        messages.error(request, 'An unexpected error occurred')
        return render(request, 'form.html', context)
```

### Transaction Rollback

**All service methods** use this pattern:
```python
from django.db import transaction

@transaction.atomic
def create_supplier_bill(...):
    try:
        # Business logic
        pass
    except Exception:
        # Transaction automatically rolls back
        raise
```

### Logging Strategy

```python
import logging
logger = logging.getLogger('efbm.payables')

# Log all financial operations
logger.info(f'Bill {bill_number} created by {user}')
logger.warning(f'Bill {bill_number} approval failed: {reason}')
logger.error(f'Journal posting failed for bill {bill_number}', exc_info=True)
```


## Performance Optimization

### Database Query Optimization

**Use select_related() for ForeignKey**:
```python
bills = SupplierBill.objects.filter(
    tenant=tenant
).select_related(
    'supplier'
).prefetch_related(
    'approvals__approval_level',
    'approvals__approver'
)
```

**Database Indexes**:
```python
class SupplierBill(TenantBaseModel):
    class Meta:
        indexes = [
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['tenant', 'supplier', 'bill_number']),
            models.Index(fields=['tenant', 'due_date']),
            models.Index(fields=['created_at']),
        ]
```

### Caching Strategy (Future Phase)

- Cache supplier list for dropdown (1 hour TTL)
- Cache approval matrix configuration (1 day TTL)
- Cache account mapping (1 day TTL)

### Pagination

- List view: 50 bills per page
- Audit trail: 100 entries per page
- Use Django Paginator with optimized queries

## Security Considerations

### Authentication & Authorization

**Required Permissions**:
```python
# Permission model (to be implemented with django.contrib.auth)
- efbm.add_supplierbill
- efbm.change_supplierbill
- efbm.delete_supplierbill
- efbm.approve_supplierbill
- efbm.cancel_supplierbill
```

**View-Level Checks**:
```python
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

class SupplierBillCreateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'efbm.add_supplierbill'
```

### Input Validation

- Sanitize all user inputs
- Validate file uploads (type, size, virus scan)
- Prevent SQL injection (use ORM queries)
- Prevent XSS (template auto-escaping)
- CSRF protection (Django middleware)

### Multi-Tenant Isolation

**Critical Rule**: Every query MUST include tenant filter
```python
# CORRECT
bills = SupplierBill.objects.filter(tenant=request.tenant)

# WRONG - SECURITY VULNERABILITY
bills = SupplierBill.objects.all()
```


## Migration Plan

### New Migration: Add Fields to SupplierBill

**File**: `backend/apps/efbm/migrations/0009_enhance_supplier_bill.py`

**Changes**:
1. Add `supplier` ForeignKey to Supplier model
2. Add `subtotal` DecimalField
3. Add `tax_amount` DecimalField  
4. Rename `amount` to `total_amount` (or keep both for backward compatibility)
5. Add `description` TextField
6. Add `submitted_at` DateTimeField(null=True)
7. Add `approved_at` DateTimeField(null=True)
8. Add new status choices: 'draft', 'submitted'
9. Add indexes for performance

**Data Migration**:
- Migrate existing bills: find supplier by supplier_name
- Set subtotal = amount, tax_amount = 0, total_amount = amount
- Set status = 'pending' → 'draft' for backward compatibility

### New Migration: Create SupplierBillAudit Model

**File**: `backend/apps/efbm/migrations/0010_add_supplier_bill_audit.py`

**Changes**:
1. Create SupplierBillAudit model
2. Add indexes for query performance

## Deployment Checklist

### Pre-Deployment
- [ ] All tests passing (unit + integration)
- [ ] Code review completed
- [ ] Migration files generated
- [ ] Migration tested on staging database
- [ ] Performance benchmarks met
- [ ] Security audit completed
- [ ] Documentation updated

### Deployment Steps
1. Backup production database
2. Deploy code to staging
3. Run migrations on staging: `python manage.py migrate`
4. Test core workflows on staging
5. Deploy to production
6. Run migrations on production
7. Monitor error logs for 24 hours
8. Verify with production smoke tests

### Post-Deployment
- [ ] Monitor application logs
- [ ] Check database performance
- [ ] Verify multi-tenant isolation
- [ ] Test approval workflow with real users
- [ ] Collect user feedback


## Implementation Order

To minimize integration issues, implement in this order:

### Phase 2.1: Foundation (Day 1-2)
1. Create SupplierBillAudit model and migration
2. Enhance SupplierBill model with new fields and migration
3. Run and test migrations
4. Implement helper methods (_create_audit_log, _update_supplier_ledger)

### Phase 2.2: Core Service Methods (Day 3-5)
1. Implement create_supplier_bill()
2. Implement update_supplier_bill()
3. Implement submit_supplier_bill() and _initiate_approval_workflow()
4. Write unit tests for above methods

### Phase 2.3: Approval Workflow (Day 6-7)
1. Implement approve_supplier_bill()
2. Implement reject_supplier_bill()
3. Implement cancel_supplier_bill()
4. Write unit tests for approval workflow
5. Integration tests with journal posting

### Phase 2.4: View Layer (Day 8-9)
1. Implement SupplierBillListView
2. Implement SupplierBillCreateView
3. Implement SupplierBillDetailView
4. Implement SupplierBillUpdateView
5. Add URL routes

### Phase 2.5: Templates (Day 10-11)
1. Create supplier_bills.html (list)
2. Create supplier_bill_form.html (create/edit)
3. Create supplier_bill_detail.html (detail)
4. Add HTMX interactions

### Phase 2.6: Testing & QA (Day 12-14)
1. Complete test suite
2. Integration testing
3. Performance testing
4. Security audit
5. Code review
6. Bug fixes

### Phase 2.7: Documentation & Deployment (Day 15)
1. Update README
2. Create user documentation
3. Staging deployment
4. Production deployment
5. User training

## Success Criteria

Implementation is complete when:
- ✅ All 10 functional requirements met
- ✅ All 6 non-functional requirements met
- ✅ Test coverage > 80%
- ✅ All tests passing
- ✅ `python manage.py check` passes
- ✅ Code review approved
- ✅ Successfully deployed to production
- ✅ Zero critical bugs in first week

