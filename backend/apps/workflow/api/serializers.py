from rest_framework import serializers
from backend.apps.workflow.models import (
    WorkflowDefinition, WorkflowVersion, WorkflowStep, WorkflowInstance, WorkflowTask, WorkflowApproval, ApprovalDelegation, Document, DocumentVersion
)

class DefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowDefinition
        fields = ['id', 'name', 'trigger_event']


class VersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowVersion
        fields = ['id', 'workflow', 'version_number', 'is_published']


class StepSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowStep
        fields = ['id', 'version', 'step_order', 'role_required']


class InstanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowInstance
        fields = ['id', 'version', 'target_id', 'status']


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowTask
        fields = ['id', 'instance', 'step', 'assigned_role', 'is_completed']


class ApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowApproval
        fields = ['id', 'task', 'approver', 'decision', 'comments', 'timestamp']


class DelegationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApprovalDelegation
        fields = ['id', 'original_approver', 'delegated_approver', 'start_date', 'end_date']


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['id', 'name', 'file_path']
