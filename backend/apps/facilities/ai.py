from abc import ABC, abstractmethod

class IAIMaintenancePredictor(ABC):
    """
    Interface for predicting next HVAC/AC breakdowns.
    """
    @abstractmethod
    def predict_failure_probability(self, facility_id: str) -> float:
        pass


class IAIFacilityHealthAnalyzer(ABC):
    """
    Interface for assessing a building health score based on work requests.
    """
    @abstractmethod
    def calculate_health_index(self, building_id: str) -> float:
        pass


class IAIEnergyOptimizer(ABC):
    """
    Interface for suggesting dynamic cooling temperature settings to reduce bills.
    """
    @abstractmethod
    def recommend_energy_adjustments(self, building_id: str) -> list:
        pass


class IAIWorkOrderPrioritizer(ABC):
    """
    Interface for automatically prioritizing work request descriptions.
    """
    @abstractmethod
    def classify_priority(self, description_text: str) -> str:
        pass
