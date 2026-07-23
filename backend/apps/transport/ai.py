from abc import ABC, abstractmethod

class IAIRouteOptimizer(ABC):
    """
    Interface for computing shortest pickup path coordinates based on student locations.
    """
    @abstractmethod
    def optimize_route(self, student_coordinates: list) -> list:
        pass


class IAIFuelPredictor(ABC):
    """
    Interface for forecasting fuel usage trends across vehicles.
    """
    @abstractmethod
    def predict_fuel_consumption(self, vehicle_id: str, distance_km: float) -> float:
        pass


class IAIArrivalPredictor(ABC):
    """
    Interface for estimating live ETA and arrival delays.
    """
    @abstractmethod
    def predict_eta(self, vehicle_id: str, stop_id: str) -> float:
        pass


class IAIDriverBehaviorAnalyzer(ABC):
    """
    Interface for analyzing acceleration, braking, and speeding metrics.
    """
    @abstractmethod
    def analyze_driver_safety(self, driver_id: str) -> dict:
        pass
