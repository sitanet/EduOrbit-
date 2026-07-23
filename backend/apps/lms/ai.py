from abc import ABC, abstractmethod

class IAIContentGenerator(ABC):
    """
    Interface for generating AI study guides.
    """
    @abstractmethod
    def generate_learning_content(self, topic: str, target_audience: str) -> dict:
        pass


class IAILessonSummarizer(ABC):
    """
    Interface for compiling classroom summaries.
    """
    @abstractmethod
    def summarize_lesson(self, transcript_text: str) -> str:
        pass


class IAIFlashcardGenerator(ABC):
    """
    Interface for generating review flashcards.
    """
    @abstractmethod
    def generate_flashcards(self, content_body: str) -> list:
        pass


class IAIQuizGenerator(ABC):
    """
    Interface for compiling assessment questions.
    """
    @abstractmethod
    def generate_questions(self, topic: str, count: int) -> list:
        pass


class IAILearningPathGenerator(ABC):
    """
    Interface for suggesting customized student learning paths.
    """
    @abstractmethod
    def recommend_remediations(self, progress_history: list) -> list:
        pass


class IAIStudentTutor(ABC):
    """
    Interface for interactive tutor coaching.
    """
    @abstractmethod
    def chat_response(self, student_message: str, context_notes: str) -> str:
        pass


class IAIRecommendationEngine(ABC):
    """
    Interface for recommending content reading materials.
    """
    @abstractmethod
    def get_recommendations(self, student_id: str) -> list:
        pass
