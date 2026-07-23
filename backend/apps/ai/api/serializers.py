from rest_framework import serializers
from backend.apps.ai.models import (
    AIProvider, AIModel, AIConversation, AIMessage, PromptTemplate, PromptVersion, AIEmbedding, KnowledgeDocument, KnowledgeChunk, AutomationRule
)

class ProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIProvider
        fields = ['id', 'name', 'api_key', 'endpoint_url']


class ModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIModel
        fields = ['id', 'provider', 'model_name', 'context_window']


class ConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIConversation
        fields = ['id', 'user', 'title', 'created_at']


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIMessage
        fields = ['id', 'conversation', 'prompt', 'response', 'tokens_used', 'latency_ms']


class TemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromptTemplate
        fields = ['id', 'name', 'category']


class VersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromptVersion
        fields = ['id', 'template', 'version_number', 'system_instructions']


class RuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutomationRule
        fields = ['id', 'name', 'trigger_event', 'action_to_perform']
