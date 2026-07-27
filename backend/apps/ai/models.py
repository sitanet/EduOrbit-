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


# ==============================================================
# PREDICTIVE INTELLIGENCE & MODELS
# ==============================================================

class PredictiveModel(TenantBaseModel):
    name = models.CharField(max_length=150)
    target_metric = models.CharField(max_length=100)  # dropout_risk, fee_default_risk

    def __str__(self):
        return self.name


class PredictionResult(TenantBaseModel):
    model = models.ForeignKey(PredictiveModel, on_delete=models.CASCADE, related_name='results')
    subject_identifier = models.CharField(max_length=150)  # Student number or Invoice ID
    probability = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    confidence = models.DecimalField(max_digits=5, decimal_places=2, default=0.90)
    explanation = models.TextField(blank=True)
    recommended_action = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Prediction: {self.model.name} for {self.subject_identifier} (Prob: {self.probability})"


# ==============================================================
# AI AUDIT LOGS, USAGE & RECOMMENDATIONS
# ==============================================================

class AITokenUsage(TenantBaseModel):
    provider_name = models.CharField(max_length=100)
    model_name = models.CharField(max_length=100)
    prompt_tokens = models.IntegerField(default=0)
    completion_tokens = models.IntegerField(default=0)
    total_cost_usd = models.DecimalField(max_digits=8, decimal_places=4, default=0.0000)
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Usage: {self.provider_name}/{self.model_name} ({self.prompt_tokens + self.completion_tokens} tokens)"


class AIRecommendation(TenantBaseModel):
    module_category = models.CharField(max_length=50)  # HR, SIS, Finance, LMS
    title = models.CharField(max_length=200)
    description = models.TextField()
    priority = models.CharField(max_length=20, default='medium')  # low, medium, high
    status = models.CharField(max_length=20, default='pending')  # pending, accepted, dismissed

    def __str__(self):
        return f"Rec [{self.module_category}]: {self.title}"


class AIInsight(TenantBaseModel):
    domain = models.CharField(max_length=50)  # Academic, Financial, Staff
    summary = models.TextField()
    score = models.DecimalField(max_digits=5, decimal_places=2, default=95.00)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Insight ({self.domain}): {self.summary[:30]}"


class AIAuditLog(TenantBaseModel):
    user_identity = models.CharField(max_length=150)
    action_type = models.CharField(max_length=100)  # chat, predict, RAG_query
    prompt_summary = models.TextField()
    response_summary = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Audit: {self.user_identity} -> {self.action_type} at {self.timestamp}"


