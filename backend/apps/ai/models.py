import uuid
from django.db import models
from django.utils import timezone
from backend.apps.core.models import TenantBaseModel, PlatformBaseModel

# ==============================================================
# AI PROVIDERS & CONVERSATIONS
# ==============================================================

class AIProvider(PlatformBaseModel):
    name = models.CharField(max_length=100, unique=True)
    api_key = models.CharField(max_length=255, blank=True)
    endpoint_url = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.name


class AIModel(PlatformBaseModel):
    provider = models.ForeignKey(AIProvider, on_delete=models.CASCADE, related_name='models')
    model_name = models.CharField(max_length=150)
    context_window = models.IntegerField(default=4096)

    def __str__(self):
        return f"{self.provider.name} - {self.model_name}"


class AIConversation(TenantBaseModel):
    user = models.ForeignKey('identity.User', on_delete=models.CASCADE, related_name='conversations')
    title = models.CharField(max_length=150)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Chat: {self.title} ({self.user.username})"


class AIMessage(TenantBaseModel):
    conversation = models.ForeignKey(AIConversation, on_delete=models.CASCADE, related_name='messages')
    prompt = models.TextField()
    response = models.TextField()
    tokens_used = models.IntegerField(default=0)
    latency_ms = models.IntegerField(default=0)

    def __str__(self):
        return f"Msg in {self.conversation.title}"


# ==============================================================
# PROMPT LIBRARY & RAG KNOWLEDGE BASE
# ==============================================================

class PromptTemplate(TenantBaseModel):
    name = models.CharField(max_length=150)
    category = models.CharField(max_length=100)  # homework, lesson_plan

    def __str__(self):
        return self.name


class PromptVersion(TenantBaseModel):
    template = models.ForeignKey(PromptTemplate, on_delete=models.CASCADE, related_name='versions')
    version_number = models.IntegerField(default=1)
    system_instructions = models.TextField()

    def __str__(self):
        return f"{self.template.name} V{self.version_number}"


class AIEmbedding(TenantBaseModel):
    chunk_text = models.TextField()
    embedding_vector_json = models.TextField(blank=True)  # Mock representation

    def __str__(self):
        return f"Embedding: {self.chunk_text[:30]}"


class KnowledgeDocument(TenantBaseModel):
    name = models.CharField(max_length=150)
    file_path = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class KnowledgeChunk(TenantBaseModel):
    document = models.ForeignKey(KnowledgeDocument, on_delete=models.CASCADE, related_name='chunks')
    content = models.TextField()

    def __str__(self):
        return f"Chunk of {self.document.name}"


class AutomationRule(TenantBaseModel):
    """
    Intelligent event triggers (e.g. absent triggers warning letter).
    """
    name = models.CharField(max_length=150)
    trigger_event = models.CharField(max_length=100)  # student.absent
    action_to_perform = models.CharField(max_length=150)  # generate_warning

    def __str__(self):
        return self.name
