from abc import ABC, abstractmethod

class IAIPurchasePredictor(ABC):
    """
    Interface for forecasting seasonal pricing levels and bulk order sizes.
    """
    @abstractmethod
    def predict_optimal_order_quantity(self, item_sku: str) -> float:
        pass


class IAIStockForecast(ABC):
    """
    Interface for forecasting stock depletion rates based on school semesters.
    """
    @abstractmethod
    def forecast_stock_level(self, item_sku: str, days_ahead: int) -> list:
        pass


class IAIAutoReorder(ABC):
    """
    Interface for computing smart reorder thresholds based on supplier lead times.
    """
    @abstractmethod
    def calculate_reorder_point(self, item_sku: str) -> int:
        pass


class IAISupplierEvaluator(ABC):
    """
    Interface for rating supplier performance indicators.
    """
    @abstractmethod
    def evaluate_supplier_risk(self, supplier_id: str) -> dict:
        pass
