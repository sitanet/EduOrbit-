import uuid
from django.db import models
from backend.apps.core.models import TenantBaseModel

class OnboardingDraft(TenantBaseModel):
    """
    Onboarding Draft Model supporting Auto-Save (5s) and Resume Later across Steps 1 to 8.
    """
    draft_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    version = models.CharField(max_length=20, default='v1')
    created_by = models.ForeignKey('people.Person', on_delete=models.SET_NULL, null=True, blank=True)
    current_step = models.IntegerField(default=1)
    draft_data = models.JSONField(default=dict, blank=True)
    is_completed = models.BooleanField(default=False)
    auto_saved_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Draft {self.draft_id} - Step {self.current_step} ({'Completed' if self.is_completed else 'In Progress'})"
