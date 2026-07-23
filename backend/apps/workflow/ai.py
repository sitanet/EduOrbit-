from abc import ABC, abstractmethod

class IAIWorkflowOptimizer(ABC):
    """
    Interface for suggesting modifications to step layouts based on delay trends.
    """
    @abstractmethod
    def suggest_improvements(self, workflow_id: str) -> list:
        pass


class IAIApprovalPredictor(ABC):
    """
    Interface for estimating approvals timelines and escalation hazards.
    """
    @abstractmethod
    def predict_approval_time_hours(self, task_id: str) -> float:
        pass


class IAIDocumentClassifier(ABC):
    """
    Interface for tagging uploaded documents automatically.
    """
    @abstractmethod
    def classify_document(self, content_stream: str) -> dict:
        pass


class IAISLAAdvisor(ABC):
    """
    Interface for suggesting dynamic timeout thresholds for roles.
    """
    @abstractmethod
    def suggest_sla_days(self, step_id: str) -> float:
        pass
