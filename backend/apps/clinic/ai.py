from abc import ABC, abstractmethod

class IAIDiagnosisAssistant(ABC):
    """
    Interface for recommending potential diagnoses based on symptoms checkouts.
    """
    @abstractmethod
    def suggest_diagnosis(self, symptoms_text: str) -> list:
        pass


class IAITriageAssistant(ABC):
    """
    Interface for prioritizing clinic queue based on vitals metrics.
    """
    @abstractmethod
    def evaluate_priority(self, vitals: dict) -> str:
        pass


class IAIMedicationInteractionChecker(ABC):
    """
    Interface for checking drug interactions warnings before prescription checkout.
    """
    @abstractmethod
    def check_interaction(self, drug_ids: list) -> list:
        pass


class IAIHealthRiskPredictor(ABC):
    """
    Interface for predicting seasonal flu or chronic disease spikes across students.
    """
    @abstractmethod
    def predict_risk(self, school_id: str) -> dict:
        pass
