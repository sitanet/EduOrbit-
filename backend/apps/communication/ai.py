from abc import ABC, abstractmethod

class IAIAnnouncementWriter(ABC):
    """
    Interface for drafting high-priority announcements and emergency alerts.
    """
    @abstractmethod
    def draft_announcement(self, topic: str, priority_level: str) -> str:
        pass


class IAITranslator(ABC):
    """
    Interface for translating message templates into preferred regional languages.
    """
    @abstractmethod
    def translate_message(self, text: str, target_lang: str) -> str:
        pass


class IAIMessageRewriter(ABC):
    """
    Interface for improving tone and grammar in chats.
    """
    @abstractmethod
    def rewrite_message(self, text: str, tone: str) -> str:
        pass


class IAISummarizer(ABC):
    """
    Interface for condensing long newsletters or announcements into quick summaries.
    """
    @abstractmethod
    def summarize_content(self, text: str) -> str:
        pass


class IAIAutoResponder(ABC):
    """
    Interface for answering simple parent FAQs.
    """
    @abstractmethod
    def generate_reply(self, message_text: str) -> str:
        pass


class IAISentimentAnalyzer(ABC):
    """
    Interface for evaluating parents feedback sentiment metrics.
    """
    @abstractmethod
    def analyze_sentiment(self, text: str) -> dict:
        pass
