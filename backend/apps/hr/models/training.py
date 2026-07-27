import uuid
from django.db import models
from backend.apps.core.models import TenantBaseModel

class TrainingProgram(TenantBaseModel):
    name = models.CharField(max_length=150)
    cost = models.DecimalField(max_digits=12, decimal_places=2)
    cpd_hours = models.IntegerField(default=0)

    def __str__(self):
        return self.name
