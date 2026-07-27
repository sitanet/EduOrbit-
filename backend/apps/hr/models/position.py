from django.db import models
from backend.apps.core.models import TenantBaseModel

class JobPosition(TenantBaseModel):
    """
    Decoupled Position Management entity tracking headcount limits, filled, and vacant seats.
    """
    title = models.CharField(max_length=150)
    code = models.CharField(max_length=50, unique=True)
    department_name = models.CharField(max_length=150, default='General Academics')
    campus_name = models.CharField(max_length=150, default='Main Campus')
    cost_centre = models.CharField(max_length=100, default='CC-101-ACADEMICS')
    max_headcount = models.PositiveIntegerField(default=1)
    filled_headcount = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    @property
    def vacant_headcount(self):
        return max(0, self.max_headcount - self.filled_headcount)

    def __str__(self):
        return f"{self.title} ({self.filled_headcount}/{self.max_headcount} Filled)"
