import uuid
from django.db import models
from django.utils import timezone
from backend.apps.core.models import PlatformBaseModel, TenantBaseModel

# ==============================================================
# TENANT & SCHOOL SCHEMAS
# ==============================================================

class Tenant(PlatformBaseModel):
    """
    Tenant Organization representing the corporate group (e.g., Grace Education Group).
    Accounts are mapped at the organization level.
    """
    BILLING_MODELS = [
        ('PARENT_PAYS', 'Model A (Parent Pays)'),
        ('SCHOOL_PAYS', 'Model B (School Pays)'),
        ('HYBRID', 'Model C (Hybrid Billing)')
    ]
    name = models.CharField(max_length=255)
    legal_name = models.CharField(max_length=255, blank=True)
    registration_number = models.CharField(max_length=100, blank=True)
    tax_number = models.CharField(max_length=100, blank=True)
    
    # Billing Setup
    billing_model = models.CharField(max_length=20, choices=BILLING_MODELS, default='PARENT_PAYS')
    parent_subscription_amount = models.DecimalField(max_digits=12, decimal_places=2, default=5000.00, help_text="Termly fee per child")
    compliance_threshold_percent = models.DecimalField(max_digits=5, decimal_places=2, default=80.00)
    billing_status = models.CharField(
        max_length=20,
        choices=[
            ('ACTIVE', 'Active'),
            ('GRACE_PERIOD', 'Grace Period'),
            ('RESTRICTED', 'Restricted'),
            ('SUSPENDED', 'Suspended')
        ],
        default='ACTIVE'
    )
    
    # Branding configurations (white-label details)
    branding_config = models.JSONField(default=dict, blank=True)
    # Storage settings overrides (inherit S3/GCS or local)
    settings_override = models.JSONField(default=dict, blank=True)
    
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name = 'Tenant'
        verbose_name_plural = 'Tenants'

    def __str__(self):
        return self.name


class School(TenantBaseModel):
    """
    Specific Educational Institution under an Organization (Tenant).
    (e.g., Grace Nursery School, Grace College).
    """
    name = models.CharField(max_length=255)
    school_types = models.JSONField(default=list, help_text="e.g. ['creche', 'preschool', 'secondary']")
    curriculum_codes = models.JSONField(default=list, help_text="List of curriculum codes: ['nigerian', 'cambridge']")
    is_active = models.BooleanField(default=True, db_index=True)

    def __str__(self):
        return f"{self.name} ({self.tenant.name})"


# ==============================================================
# CAMPUS & BRANCH SCHEMAS
# ==============================================================

class Campus(TenantBaseModel):
    """
    Campus location under a specific School.
    """
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='campuses')
    name = models.CharField(max_length=255)
    address = models.TextField()
    contact_phone = models.CharField(max_length=30, blank=True)
    contact_email = models.EmailField(blank=True)
    principal_user_id = models.UUIDField(null=True, blank=True)
    branding_override = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.name} - {self.school.name}"


class Branch(TenantBaseModel):
    """
    Sub-branch location under a specific Campus.
    """
    campus = models.ForeignKey(Campus, on_delete=models.CASCADE, related_name='branches')
    name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name} - {self.campus.name}"


# ==============================================================
# SUBSCRIPTION & BILLING SCHEMAS
# ==============================================================

class SubscriptionPlan(PlatformBaseModel):
    """
    Platform recurring subscription packages supporting School Pay, Parent Pay, and Hybrid models.
    """
    BILLING_MODELS = [
        ('PARENT_PAYS', 'Parent Pay'),
        ('SCHOOL_PAYS', 'School Pay'),
        ('HYBRID', 'Hybrid')
    ]
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    billing_model = models.CharField(max_length=20, choices=BILLING_MODELS, default='PARENT_PAYS')
    
    monthly_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    termly_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    yearly_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # Tier Pricing Formula for SCHOOL_PAYS model
    student_tier_rates = models.JSONField(
        default=dict,
        blank=True,
        help_text="JSON format for tier rates, e.g. {'1-200': 2000, '201-500': 1500, '501-1000': 1200, '1001+': 1000}"
    )
    
    trial_days = models.IntegerField(default=14)
    grace_period_days = models.IntegerField(default=7)
    max_students = models.IntegerField(default=500)
    max_staff = models.IntegerField(default=50)
    max_campuses = models.IntegerField(default=1)
    
    parent_portal_enabled = models.BooleanField(default=True)
    mobile_app_enabled = models.BooleanField(default=True)
    lms_enabled = models.BooleanField(default=True)
    cbt_enabled = models.BooleanField(default=True)
    is_custom = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    features = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.name} ({self.billing_model})"


class TenantSubscription(TenantBaseModel):
    """
    Licenses and active subscriptions per Tenant (Organization/School).
    Used for SCHOOL_PAYS model or School-level activation.
    """
    STATUS_CHOICES = [
        ('TRIAL', 'Trial'),
        ('ACTIVE', 'Active'),
        ('EXPIRING_SOON', 'Expiring Soon'),
        ('DUE_TODAY', 'Due Today'),
        ('GRACE_PERIOD', 'Grace Period'),
        ('EXPIRED', 'Expired'),
        ('SUSPENDED', 'Suspended'),
        ('CANCELLED', 'Cancelled')
    ]
    BILLING_CYCLES = [
        ('MONTHLY', 'Monthly'),
        ('TERMLY', 'Termly'),
        ('YEARLY', 'Yearly')
    ]
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE, null=True, blank=True)
    billing_model = models.CharField(max_length=20, default='PARENT_PAYS')
    billing_cycle = models.CharField(max_length=20, choices=BILLING_CYCLES, default='TERMLY')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    
    active_student_count = models.IntegerField(default=0)
    calculated_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()
    grace_period_ends_at = models.DateTimeField(null=True, blank=True)
    last_payment_date = models.DateTimeField(null=True, blank=True)
    next_renewal_date = models.DateTimeField(null=True, blank=True)
    auto_renew = models.BooleanField(default=True)
    payment_provider = models.CharField(max_length=50, default='Paystack')
    
    modules_licensed = models.JSONField(default=dict, blank=True)
    renewal_history = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f"{self.tenant.name} - {self.plan.name if self.plan else 'Custom'} ({self.status})"

    def is_active_license(self) -> bool:
        if self.status in ['SUSPENDED', 'CANCELLED']:
            return False
        now = timezone.now()
        return self.end_date > now or (self.grace_period_ends_at and self.grace_period_ends_at > now)


class ParentSubscription(TenantBaseModel):
    """
    Single subscription per Parent Account activating ALL linked children.
    Total amount is calculated based on: fee_per_child * child_count
    (e.g., ₦500 per child x 2 children = ₦1,000 total).
    """
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('UNPAID', 'Unpaid'),
        ('OVERDUE', 'Overdue'),
        ('CANCELLED', 'Cancelled')
    ]
    parent = models.ForeignKey('people.ParentProfile', on_delete=models.CASCADE, related_name='platform_subscriptions')
    academic_year = models.ForeignKey('academic.AcademicYear', on_delete=models.SET_NULL, null=True, blank=True)
    academic_period = models.ForeignKey('academic.AcademicPeriod', on_delete=models.SET_NULL, null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='UNPAID')
    child_count = models.IntegerField(default=1, help_text="Number of children linked to parent")
    fee_per_child = models.DecimalField(max_digits=12, decimal_places=2, default=5000.00, help_text="Base fee per child")
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="Total amount = fee_per_child * child_count")
    
    paid_until = models.DateTimeField(null=True, blank=True)
    invoice = models.ForeignKey('SubscriptionInvoice', on_delete=models.SET_NULL, null=True, blank=True, related_name='parent_subscriptions')

    class Meta:
        verbose_name = 'Parent Subscription'
        verbose_name_plural = 'Parent Subscriptions'
        unique_together = ('tenant', 'parent', 'academic_period')

    def calculate_total_amount(self) -> Decimal:
        """
        Calculates total parent subscription amount based on child count.
        e.g., 500 per child x 2 children = 1000 total.
        """
        self.amount = self.fee_per_child * Decimal(str(self.child_count))
        return self.amount

    def save(self, *args, **kwargs):
        self.calculate_total_amount()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Parent Sub: {self.parent.parent_number} ({self.child_count} children = ₦{self.amount})"


class StudentPlatformSubscription(TenantBaseModel):
    """
    Direct student platform subscription reference mapping.
    """
    student = models.ForeignKey('people.StudentProfile', on_delete=models.CASCADE, related_name='platform_subscriptions')
    parent_subscription = models.ForeignKey(ParentSubscription, on_delete=models.CASCADE, null=True, blank=True, related_name='activated_students')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE, null=True, blank=True)
    billing_cycle = models.CharField(max_length=20, default='TERMLY')
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    paid_until = models.DateTimeField(null=True, blank=True)
    payment_status = models.CharField(max_length=20, default='ACTIVE')
    payment_reference = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Student Sub: {self.student.student_number} ({self.payment_status})"


# ==============================================================
# INVOICE, PAYMENT & AUDIT LOG SCHEMAS
# ==============================================================

class SubscriptionInvoice(TenantBaseModel):
    """
    Generated Invoices for School or Parent subscriptions.
    """
    INVOICE_TYPES = [
        ('SCHOOL', 'School Activation Invoice'),
        ('PARENT', 'Parent Access Invoice')
    ]
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PENDING', 'Pending Payment'),
        ('PAID', 'Paid'),
        ('OVERDUE', 'Overdue'),
        ('CANCELLED', 'Cancelled')
    ]
    invoice_number = models.CharField(max_length=100, unique=True, db_index=True)
    invoice_type = models.CharField(max_length=20, choices=INVOICE_TYPES, default='PARENT')
    
    school = models.ForeignKey(School, on_delete=models.CASCADE, null=True, blank=True)
    tenant_subscription = models.ForeignKey(TenantSubscription, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    due_date = models.DateTimeField()
    paid_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.invoice_number} ({self.status})"


class SubscriptionPayment(TenantBaseModel):
    """
    Transaction records for online Paystack and manual school payment options.
    """
    PAYMENT_METHODS = [
        ('PAYSTACK', 'Paystack Online'),
        ('CASH', 'Cash'),
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('POS', 'POS Terminal'),
        ('CHEQUE', 'Cheque')
    ]
    STATUS_CHOICES = [
        ('INITIATED', 'Initiated'),
        ('SUCCESSFUL', 'Successful'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded')
    ]
    reference = models.CharField(max_length=100, unique=True, db_index=True)
    invoice = models.ForeignKey(SubscriptionInvoice, on_delete=models.CASCADE, related_name='payments')
    gateway = models.CharField(max_length=50, default='Paystack')
    payment_method = models.CharField(max_length=30, choices=PAYMENT_METHODS, default='PAYSTACK')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='INITIATED')
    receipt_number = models.CharField(max_length=100, unique=True, null=True, blank=True)
    
    paid_by = models.ForeignKey('identity.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='payments_processed')
    paid_on_behalf = models.BooleanField(default=False, help_text="True if school admin processed payment on behalf of parent")
    paid_at = models.DateTimeField(null=True, blank=True)
    raw_response = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"Payment {self.reference} - {self.status}"


class SubscriptionAuditLog(TenantBaseModel):
    """
    Immutable Audit Log of every subscription event, payment, manual override, and activation.
    """
    ACTION_CHOICES = [
        ('CREATED', 'Created'),
        ('UPDATED', 'Updated'),
        ('RENEWED', 'Renewed'),
        ('SUSPENDED', 'Suspended'),
        ('ACTIVATED', 'Activated'),
        ('PAYMENT', 'Payment Received'),
        ('MANUAL_OVERRIDE', 'Manual Override'),
        ('REMINDER', 'Reminder Sent')
    ]
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    tenant_subscription = models.ForeignKey(TenantSubscription, on_delete=models.SET_NULL, null=True, blank=True)
    parent_subscription = models.ForeignKey(ParentSubscription, on_delete=models.SET_NULL, null=True, blank=True)
    invoice = models.ForeignKey(SubscriptionInvoice, on_delete=models.SET_NULL, null=True, blank=True)
    payment = models.ForeignKey(SubscriptionPayment, on_delete=models.SET_NULL, null=True, blank=True)
    
    actor = models.ForeignKey('identity.User', on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Audit {self.action} @ {self.timestamp}"


class BillingSettings(PlatformBaseModel):
    """
    Platform-wide default billing configurations.
    Does NOT store Paystack Secret Keys (Keys stored ONLY in environment variables).
    """
    reminder_schedule_days = models.JSONField(
        default=list,
        help_text="List of reminder threshold days before expiry: [30, 14, 7, 3, 1, 0]"
    )
    grace_period_days_default = models.IntegerField(default=7)
    currency = models.CharField(max_length=10, default='NGN')
    invoice_prefix = models.CharField(max_length=20, default='INV-')
    receipt_prefix = models.CharField(max_length=20, default='REC-')
    compliance_default_percent = models.DecimalField(max_digits=5, decimal_places=2, default=80.00)

    class Meta:
        verbose_name = 'Billing Setting'
        verbose_name_plural = 'Billing Settings'

    def __str__(self):
        return f"Global Billing Settings ({self.currency})"


# ==============================================================
# CUSTOM DOMAIN SCHEMAS
# ==============================================================

class CustomDomain(TenantBaseModel):
    """
    Verified custom web domains pointing to this tenant.
    """
    domain_name = models.CharField(max_length=255, unique=True, db_index=True)
    is_verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=100, default=uuid.uuid4)
    ssl_active = models.BooleanField(default=False)

    def __str__(self):
        return self.domain_name
