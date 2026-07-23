from abc import ABC, abstractmethod

class IAILessonPlanner(ABC):
    """
    Interface for generating AI lesson plan assists.
    """
    @abstractmethod
    def generate_lesson_plan(self, topic: str, objectives: str) -> dict:
        pass


class IAIHomeworkGenerator(ABC):
    """
    Interface for generating AI classroom homework tasks.
    """
    @abstractmethod
    def generate_homework(self, topic: str, difficulty: str) -> dict:
        pass


class IAICurriculumMapper(ABC):
    """
    Interface for checking curriculum alignments.
    """
    @abstractmethod
    def check_alignment(self, lesson_content: str, curriculum_objectives: list) -> bool:
        pass


class IAIQuizGenerator(ABC):
    """
    Interface for generating AI quiz assessments.
    """
    @abstractmethod
    def generate_quiz(self, topic: str, question_count: int) -> list:
        pass


class IAILessonSummary(ABC):
    """
    Interface for generating summary reports of delivered lesson instances.
    """
    @abstractmethod
    def summarize_lesson(self, transcript_or_notes: str) -> str:
        pass


class IAITeachingCoach(ABC):
    """
    Interface for delivering teaching insights based on journals.
    """
    @abstractmethod
    def analyze_journals(self, journal_entries: list) -> dict:
        pass
