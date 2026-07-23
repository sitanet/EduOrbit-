from abc import ABC, abstractmethod

class IAIPaymentPredictor(ABC):
    """
    Interface for predicting cash flow timing and parent payment milestones.
    """
    @abstractmethod
    def predict_payment_date(self, parent_id: str, invoice_id: str) -> str:
        pass


class IAIDefaulterPredictor(ABC):
    """
    Interface for identifying parents at high risk of tuition fee defaults.
    """
    @abstractmethod
    def evaluate_default_risk(self, parent_id: str) -> dict:
        pass


class IAIRevenueAnalyzer(ABC):
    """
    Interface for analyzing school seasonal revenue collections indices.
    """
    @abstractmethod
    def analyze_revenue_trends(self, school_id: str) -> dict:
        pass


class IAIFeeOptimizer(ABC):
    """
    Interface for suggesting dynamic price optimizations for fee items.
    """
    @abstractmethod
    def recommend_fee_pricing(self, category_code: str) -> dict:
        pass


class IAIScholarshipAdvisor(ABC):
    """
    Interface for evaluating scholarship award eligibility.
    """
    @abstractmethod
    def analyze_eligibility(self, student_id: str) -> dict:
        pass


class IAIFraudDetector(ABC):
    """
    Interface for auditing double postings or suspicious ledger changes.
    """
    @abstractmethod
    def audit_ledgers(self, school_id: str) -> list:
        pass
