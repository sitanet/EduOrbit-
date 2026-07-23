from abc import ABC, abstractmethod

class IAIPredictiveAnalytics(ABC):
    """
    Interface for evaluating multidimensional student risk metrics.
    """
    @abstractmethod
    def evaluate_predictive_trends(self, tenant_id: str) -> dict:
        pass


class IAIAcademicAdvisor(ABC):
    """
    Interface for generating learning tips based on CBT performances.
    """
    @abstractmethod
    def recommend_academic_interventions(self, student_id: str) -> list:
        pass


class IAIFinancialForecaster(ABC):
    """
    Interface for predicting next term's cashflow and fee collections.
    """
    @abstractmethod
    def forecast_cashflow(self, tenant_id: str) -> dict:
        pass


class IAIExecutiveNarrator(ABC):
    """
    Interface for summarizing school metrics into a readable report text.
    """
    @abstractmethod
    def write_executive_summary(self, school_id: str) -> str:
        pass


class IAIDropoutPredictor(ABC):
    """
    Interface for evaluating school dropout risks based on absent scores.
    """
    @abstractmethod
    def identify_at_risk_students(self, school_id: str) -> list:
        pass
