import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from backend.apps.core.models import PlatformBaseModel, TenantBaseModel

# ==============================================================
# USER MANAGER & USER MODEL
# ==============================================================

class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('email_verified', True)
        return self.create_user(username, email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Enterprise Custom User Model. Accounts exist globally and link to schools via TenantMembership.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=150, unique=True, db_index=True)
    email = models.EmailField(unique=True, db_index=True)
    phone_number = models.CharField(max_length=30, blank=True, null=True, db_index=True)
    profile_photo = models.ImageField(upload_to='profiles/photos/', null=True, blank=True)
    
    # Custom status and system validation flags
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    mfa_enabled = models.BooleanField(default=False)
    
    # Security tracking parameters
    failed_login_attempts = models.IntegerField(default=0)
    account_locked_until = models.DateTimeField(null=True, blank=True)
    password_changed_at = models.DateTimeField(default=timezone.now)
    
    # Preferred user settings configurations
    preferred_language = models.CharField(max_length=10, default='en')
    timezone = models.CharField(max_length=50, default='UTC')
    theme_preference = models.CharField(max_length=20, default='light')
    
    # platform-base tracking fields built-in directly
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    created_by = models.UUIDField(null=True, blank=True)
    updated_by = models.UUIDField(null=True, blank=True)
    deleted_by = models.UUIDField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']

    def __str__(self):
        return self.username

    def get_full_name(self) -> str:
        """
        Return full name from linked Person profile, or username as fallback.
        Compatible with Django's standard auth template patterns.
        """
        try:
            person = getattr(self, 'person_profile', None)
            if person:
                name = person.get_full_name()
                if name:
                    return name
        except Exception:
            pass
        return self.username

    def get_short_name(self) -> str:
        """Return first name from Person profile, or username."""
        try:
            person = getattr(self, 'person_profile', None)
            if person:
                return person.get_short_name() or self.username
        except Exception:
            pass
        return self.username


# ==============================================================
# PASSWORD & MFA MODELS
# ==============================================================

class PasswordHistory(PlatformBaseModel):
    """
    Retains secure pbkdf2/argon2 hashes of user's past passwords to prevent reuse.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="password_history")
    password_hash = models.CharField(max_length=255)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Password History Entry"
        verbose_name_plural = "Password History Entries"


class MfaAuthenticator(PlatformBaseModel):
    """
    TOTP and other Multi-Factor Authentication setups.
    """
    MFA_TYPES = [
        ('totp', 'Authenticator App (TOTP)'),
        ('email', 'Email OTP'),
        ('sms', 'SMS OTP')
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="authenticators")
    auth_type = models.CharField(max_length=20, choices=MFA_TYPES, default='totp')
    secret_key = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    backup_codes = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.auth_type}"


# ==============================================================
# RBAC SCHEMAS
# ==============================================================

class Permission(PlatformBaseModel):
    """
    Granular user actions permission profile with categorizations and UI config helpers.
    """
    code = models.CharField(max_length=100, unique=True, db_index=True)  # e.g. 'students.create'
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    module = models.CharField(max_length=100, db_index=True)  # e.g. 'Students', 'Hostel'
    category = models.CharField(max_length=100, blank=True)  # e.g. 'Academic', 'Administrative'
    is_system = models.BooleanField(default=False)
    is_tenant_configurable = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.module} - {self.name} ({self.code})"


class PermissionGroup(PlatformBaseModel):
    """
    Group of permissions mapped to simplify administration.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField(Permission, related_name="groups")

    def __str__(self):
        return self.name


class Role(PlatformBaseModel):
    """
    Predefined system roles and dynamic tenant configurations.
    """
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=100, unique=True, db_index=True)  # e.g. 'teacher', 'nurse'
    description = models.TextField(blank=True)
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, null=True, blank=True, related_name="roles")
    
    permissions = models.ManyToManyField(Permission, blank=True, related_name="roles")
    permission_groups = models.ManyToManyField(PermissionGroup, blank=True, related_name="roles")

    class Meta:
        unique_together = ('tenant', 'code')

    def __str__(self):
        return f"{self.name} ({self.code})"


class RoleGroup(PlatformBaseModel):
    """
    Aggregates list of roles together.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    roles = models.ManyToManyField(Role, related_name="groups")

    def __str__(self):
        return self.name


# ==============================================================
# TENANT MEMBERSHIPS
# ==============================================================

class TenantMembership(PlatformBaseModel):
    """
    User membership role mapping linking them to tenants, branches, and departments.
    Supports history tracing.
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('terminated', 'Terminated')
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="memberships")
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name="memberships")
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="memberships")
    
    # Multi-Campus organization details
    campus = models.CharField(max_length=100, blank=True)
    branch = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=100, blank=True)
    employment_type = models.CharField(max_length=50, blank=True)  # Contract, Permanent, Part-time
    
    # Status and validation lifecycles
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    primary_membership = models.BooleanField(default=False)
    
    effective_from = models.DateTimeField(default=timezone.now)
    effective_to = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'tenant', 'status']),
        ]

    def __str__(self):
        return f"{self.user.username} @ {self.tenant.name} ({self.role.name})"


# ==============================================================
# DEVICE SESSION MANAGEMENT
# ==============================================================

class UserSession(PlatformBaseModel):
    """
    Active user devices metadata and JWT refresh tokens tracking.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sessions")
    access_token_id = models.UUIDField(db_index=True)
    refresh_token_id = models.UUIDField(db_index=True)
    login_method = models.CharField(max_length=50, default='password')  # password, otp, magic_link
    
    # Device details
    device_name = models.CharField(max_length=100, blank=True)
    device_fingerprint = models.CharField(max_length=255, blank=True)
    browser = models.CharField(max_length=100, blank=True)
    operating_system = models.CharField(max_length=100, blank=True)
    
    # Geographic location
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    
    # Action timestamps
    login_time = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(default=timezone.now)
    refresh_token_expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)
    
    mfa_completed = models.BooleanField(default=False)
    trusted_device = models.BooleanField(default=False)

    class Meta:
        ordering = ['-login_time']

    def is_valid(self) -> bool:
        return self.revoked_at is None and self.refresh_token_expires_at > timezone.now()
