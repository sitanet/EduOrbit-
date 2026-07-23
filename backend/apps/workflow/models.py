import uuid
from django.db import models
from django.utils import timezone
from backend.apps.core.models import TenantBaseModel, PlatformBaseModel

# ==============================================================
# WORKFLOW DEFINITIONS & VERSIONING
# ==============================================================

class WorkflowDefinition(TenantBaseModel):
    name = models.CharField(max_length=150)
    trigger_event = models.CharField(max_length=100)  # e.g. purchase.request.created

    def __str__(self):
        return self.name


class WorkflowVersion(TenantBaseModel):
    workflow = models.ForeignKey(WorkflowDefinition, on_delete=models.CASCADE, related_name='versions')
    version_number = models.IntegerField(default=1)
    is_published = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.workflow.name} (V{self.version_number})"


class WorkflowStep(TenantBaseModel):
    version = models.ForeignKey(WorkflowVersion, on_delete=models.CASCADE, related_name='steps')
    step_order = models.IntegerField(default=1)
    role_required = models.CharField(max_length=100)  # e.g. FinanceDirector, Principal

    def __str__(self):
        return f"{self.version.workflow.name} Step {self.step_order} ({self.role_required})"


# ==============================================================
# WORKFLOW RUNTIME
# ==============================================================

class WorkflowInstance(TenantBaseModel):
    version = models.ForeignKey(WorkflowVersion, on_delete=models.CASCADE, related_name='instances')
    target_id = models.UUIDField()  # Points to target object ID (e.g., PurchaseRequest)
    status = models.CharField(max_length=30, default='in_progress')  # in_progress, approved, rejected

    def __str__(self):
        return f"Instance of {self.version} Target {self.target_id} Status {self.status}"


class WorkflowTask(TenantBaseModel):
    """
    Actionable task assigned to a user role at a specific step in the process.
    """
    instance = models.ForeignKey(WorkflowInstance, on_delete=models.CASCADE, related_name='tasks')
    step = models.ForeignKey(WorkflowStep, on_delete=models.CASCADE)
    assigned_role = models.CharField(max_length=100)
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return f"Task for {self.assigned_role} on Step {self.step.step_order}"


class WorkflowApproval(TenantBaseModel):
    """
    Immutable audit signatures capturing final decisions.
    """
    task = models.ForeignKey(WorkflowTask, on_delete=models.CASCADE, related_name='approvals')
    approver = models.ForeignKey('people.Person', on_delete=models.CASCADE)
    decision = models.CharField(max_length=30)  # approve, reject, return
    comments = models.TextField(blank=True)
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Approval on {self.task} by {self.approver.person_number}: {self.decision}"


# ==============================================================
# DELEGATIONS & DOCUMENT VERSIONING
# ==============================================================

class ApprovalDelegation(TenantBaseModel):
    original_approver = models.ForeignKey('people.Person', on_delete=models.CASCADE, related_name='delegations_from')
    delegated_approver = models.ForeignKey('people.Person', on_delete=models.CASCADE, related_name='delegations_to')
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return f"Delegation: {self.original_approver.person_number} -> {self.delegated_approver.person_number}"


class Document(TenantBaseModel):
    name = models.CharField(max_length=150)
    file_path = models.CharField(max_length=255)  # Spaces cloud file key

    def __str__(self):
        return self.name


class DocumentVersion(TenantBaseModel):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='versions')
    version_number = models.IntegerField(default=1)
    uploaded_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.document.name} V{self.version_number}"
