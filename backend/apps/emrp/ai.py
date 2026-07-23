from abc import ABC, abstractmethod

class IAIResultAnalyzer(ABC):
    """
    Interface for identifying anomalies in grade distribution or class marking variances.
    """
    @abstractmethod
    def analyze_results(self, exam_id: str) -> dict:
        pass


class IAIRemarkGenerator(ABC):
    """
    Interface for generating customized student remarks logs based on results.
    """
    @abstractmethod
    def generate_remarks(self, student_id: str, results_payload: list) -> str:
        pass


class IAIPromotionAdvisor(ABC):
    """
    Interface for analyzing progression trends and summer school conditions.
    """
    @abstractmethod
    def evaluate_promotion(self, student_id: str) -> dict:
        pass


class IAIPerformancePredictor(ABC):
    """
    Interface for forecasting upcoming external exams (WAEC/Cambridge) outcomes.
    """
    @abstractmethod
    def predict_performance(self, student_id: str) -> dict:
        pass


class IAITranscriptAdvisor(ABC):
    """
    Interface for auditing credit transfers validations.
    """
    @abstractmethod
    def evaluate_credits(self, student_id: str) -> dict:
        pass


class IAIRiskDetector(ABC):
    """
    Interface for flagging dropout candidates early.
    """
    @abstractmethod
    def flag_at_risk(self, student_id: str) -> bool:
        pass
