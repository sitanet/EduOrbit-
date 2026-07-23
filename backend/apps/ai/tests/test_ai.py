from django.test import TestCase
from django.utils import timezone
from backend.apps.tenants.models import Tenant, School
from backend.apps.identity.models import User
from backend.apps.ai.models import (
    AIProvider, AIModel, AIConversation, AIMessage, PromptTemplate, PromptVersion, AIEmbedding, KnowledgeDocument, KnowledgeChunk, AutomationRule
)
from backend.apps.ai.providers import OpenAIProvider, GeminiProvider

class AIPLatformTests(TestCase):
    def setUp(self):
        # Create core configurations
        self.tenant = Tenant.objects.create(name="EAPAE Org")
        self.school = School.objects.create(tenant=self.tenant, name="EAPAE High School", school_types=["secondary"])
        
        # Identity User setup
        self.user = User.objects.create_user(
            username="ai_user",
            password="secure_password_123",
            email="ai@school.edu"
        )
        
        # Provider & Model
        self.provider = AIProvider.objects.create(
            name="OpenAI Integration"
        )
        self.model = AIModel.objects.create(
            provider=self.provider,
            model_name="gpt-5-mini",
            context_window=8192
        )
        
        # Conversation session
        self.conversation = AIConversation.objects.create(
            user=self.user,
            tenant=self.tenant,
            title="Syllabus Generation Session"
        )

    def test_provider_adapters_routing(self):
        op = OpenAIProvider()
        self.assertEqual(op.generate_response("hello"), "[OpenAI Response]: Output for prompt: 'hello'")
        
        gem = GeminiProvider()
        self.assertEqual(gem.generate_response("hello"), "[Gemini Response]: Output for prompt: 'hello'")

    def test_prompt_versioning_controls(self):
        temp = PromptTemplate.objects.create(
            tenant=self.tenant,
            name="Homework Evaluator Prompt",
            category="homework"
        )
        v1 = PromptVersion.objects.create(
            template=temp,
            tenant=self.tenant,
            version_number=1,
            system_instructions="Evaluate code for time complexity constraints"
        )
        self.assertEqual(v1.version_number, 1)

    def test_rag_knowledge_chunks(self):
        doc = KnowledgeDocument.objects.create(
            tenant=self.tenant,
            name="Syllabus Manual 2026",
            file_path="spaces/syllabus_2026.pdf"
        )
        chunk = KnowledgeChunk.objects.create(
            document=doc,
            tenant=self.tenant,
            content="Chapter 3 details chemistry labs guidelines."
        )
        self.assertEqual(chunk.document.name, "Syllabus Manual 2026")

    def test_automation_rules_events(self):
        rule = AutomationRule.objects.create(
            tenant=self.tenant,
            name="Auto Warning Mail",
            trigger_event="student.absent",
            action_to_perform="send_warning_letter"
        )
        self.assertEqual(rule.trigger_event, "student.absent")
