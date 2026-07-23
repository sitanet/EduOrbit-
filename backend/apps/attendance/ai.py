from abc import ABC, abstractmethod

class IAIAttendanceRiskAnalyzer(ABC):
    """
    Interface for predicting students at risk of falling below attendance policy thresholds.
    """
    @abstractmethod
    def evaluate_risk(self, student_id: str) -> dict:
        pass


class IAIAbsenteeismPredictor(ABC):
    """
    Interface for predicting potential upcoming absences.
    """
    @abstractmethod
    def predict_absence_probability(self, student_id: str, target_date: str) -> float:
        pass


class IAIAttendancePatternAnalyzer(ABC):
    """
    Interface for detecting temporal patterns in clock-in delays (e.g. chronic Monday morning lateness).
    """
    @abstractmethod
    def analyze_patterns(self, person_id: str) -> list:
        pass


class IAIStudentWellbeingDetector(ABC):
    """
    Interface for correlating drop-offs in attendance to welfare anomalies.
    """
    @abstractmethod
    def flag_welfare_risk(self, student_id: str) -> bool:
        pass


class IAINotificationAdvisor(ABC):
    """
    Interface for suggesting customized parent check-in/absentee notifications timings.
    """
    @abstractmethod
    def draft_advice(self, student_id: str) -> str:
        pass
