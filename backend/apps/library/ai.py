from abc import ABC, abstractmethod

class IAIBookRecommendation(ABC):
    """
    Interface for predicting next books based on student reading level and checkout history.
    """
    @abstractmethod
    def suggest_books(self, student_id: str) -> list:
        pass


class IAICatalogAssistant(ABC):
    """
    Interface for answering voice search catalog queries in OPAC.
    """
    @abstractmethod
    def query_catalog(self, user_query: str) -> list:
        pass


class IAIReadingCoach(ABC):
    """
    Interface for evaluating book reviews and tracking comprehension levels.
    """
    @abstractmethod
    def evaluate_review(self, review_text: str) -> dict:
        pass


class IAIResourceClassifier(ABC):
    """
    Interface for auto-tagging digital resources by Dewey category based on contents.
    """
    @abstractmethod
    def classify_resource(self, document_text: str) -> str:
        pass
