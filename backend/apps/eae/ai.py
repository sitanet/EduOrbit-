from abc import ABC, abstractmethod

class IAIQuestionGenerator(ABC):
    """
    Interface for generating questions automatically from dynamic topics.
    """
    @abstractmethod
    def generate_question(self, topic: str, question_type: str, difficulty: str) -> dict:
        pass


class IAIDistractorGenerator(ABC):
    """
    Interface for generating incorrect options (distractors) for multiple-choice questions.
    """
    @abstractmethod
    def generate_distractors(self, question_text: str, correct_answer: str) -> list:
        pass


class IAIQuestionReviewer(ABC):
    """
    Interface for evaluating generated question items quality, bias, or curriculum alignment.
    """
    @abstractmethod
    def review_question(self, question_data: dict) -> dict:
        pass


class IAIAssessmentBuilder(ABC):
    """
    Interface for automatically constructing dynamic tests templates.
    """
    @abstractmethod
    def build_assessment(self, objective_ids: list, difficulty_ratios: dict) -> dict:
        pass


class IAIMarkingAssistant(ABC):
    """
    Interface for grading essay questions.
    """
    @abstractmethod
    def grade_essay(self, question_text: str, student_answer: str, rubric_details: str) -> dict:
        pass


class IAIIntegrityAnalyzer(ABC):
    """
    Interface for analyzing proctor logs to flag potential cheating incidents.
    """
    @abstractmethod
    def flag_suspicious_patterns(self, log_events: list) -> bool:
        pass
