from abc import ABC, abstractmethod

class IAIRoomAllocator(ABC):
    """
    Interface for optimizing room allocations based on student age, habits, or compatibility metrics.
    """
    @abstractmethod
    def assign_rooms(self, student_ids: list, room_ids: list) -> list:
        pass


class IAIOccupancyPredictor(ABC):
    """
    Interface for forecasting peak occupancy rates and bed availability gaps.
    """
    @abstractmethod
    def predict_occupancy(self, hostel_id: str, term_start_date: str) -> float:
        pass


class IAIMaintenancePredictor(ABC):
    """
    Interface for predicting room repairs needs based on historical damage logs.
    """
    @abstractmethod
    def predict_room_repairs(self, room_id: str) -> dict:
        pass


class IAIDisciplineAnalyzer(ABC):
    """
    Interface for identifying potential hostel friction zones or curfew violation patterns.
    """
    @abstractmethod
    def evaluate_behavioral_risk(self, hostel_id: str) -> dict:
        pass
