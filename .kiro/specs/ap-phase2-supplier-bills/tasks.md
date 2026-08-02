# Implementation Tasks: AP Phase 2 - Supplier Bill Management

## Task 1: Create SupplierBillAudit Model and Migration

**Description**: Create the SupplierBillAudit model for immutable audit trail tracking of all supplier bill operations.

**Acceptance Criteria**:
- Model created in `backend/apps/efbm/models.py`
- Fields: bill (FK), action, user (FK), timestamp, before_state (JSON), after_state (JSON), notes
- Migration generated and applied successfully
- Model registered in admin (optional)
- `python manage.py check` passes

**Dependencies**: None

**Estimated Time**: 2 hours

**Sub-tasks**:
1. Add SupplierBillAudit model class to models.py
2. Add proper indexes for query performance
3. Generate migration: `python manage.py makemigrations efbm`
4. Review migration file
5. Apply migration: `python manage.py migrate efbm`
6. Verify model in Django shell

---

## Task 2: Enhance SupplierBill Model with Additional Fields

**Description**: Add required fields to SupplierBill model to support full bill management workflow.

**Acceptance Criteria**:
- New fields added: supplier (FK), subtotal, tax_amount, description, submitted_at, approved_at
- Status choices updated: add 'draft', 'submitted'
- Database indexes added for performance
- Migration generated and applied
- Data migration for existing records
- `python manage.py check` passes

**Dependencies**: Task 1

**Estimated Time**: 3 hours

**Sub-tasks**:
1. Add new fields to SupplierBill model
2. Update STATUS_CHOICES
3. Add Meta.indexes for tenant+status, tenant+supplier+bill_number, tenant+due_date
4. Generate migration
5. Create data migration to populate new fields from old data
6. Test migration on copy of production data
7. Apply migration

