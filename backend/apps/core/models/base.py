import uuid
from django.db import models
from django.utils import timezone

class UUIDModel(models.Model):
    """
    Abstract model that provides a UUID4 primary key.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True

class TimestampModel(models.Model):
    """
    Abstract model that adds created_at and updated_at fields.
    """
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class SoftDeleteQuerySet(models.QuerySet):
    def delete(self):
        return super().update(is_deleted=True, deleted_at=timezone.now())

    def hard_delete(self):
        return super().delete()

    def alive(self):
        return self.filter(is_deleted=False)

    def dead(self):
        return self.filter(is_deleted=True)

class TenantManager(models.Manager):
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).alive()

    def all_with_deleted(self):
        return SoftDeleteQuerySet(self.model, using=self._db)

class SoftDeleteModel(models.Model):
    """
    Abstract model that provides soft delete capabilities.
    """
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = TenantManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=['is_deleted', 'deleted_at'])

class AuditModel(models.Model):
    """
    Abstract model that tracks user changes.
    """
    created_by = models.UUIDField(null=True, blank=True)
    updated_by = models.UUIDField(null=True, blank=True)
    deleted_by = models.UUIDField(null=True, blank=True)

    class Meta:
        abstract = True

class PlatformBaseModel(UUIDModel, TimestampModel, SoftDeleteModel, AuditModel):
    """
    Base model for platform-wide global entities (e.g. Subscription plans, countries, currencies).
    No tenant scope constraint.
    """
    class Meta:
        abstract = True

class TenantBaseModel(UUIDModel, TimestampModel, SoftDeleteModel, AuditModel):
    """
    Base model for tenant-specific scoped entities. Force-maps foreign key to tenants.Tenant.
    """
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name="%(class)ss",
        db_index=True
    )

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['tenant', 'is_deleted']),
        ]
