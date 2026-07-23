from abc import ABC, abstractmethod

class IAIResumeReviewer(ABC):
    """
    Interface for parsing and screening candidate resumes.
    """
    @abstractmethod
    def screen_resume(self, resume_text: str, job_opening_id: str) -> dict:
        pass


class IAIInterviewAssistant(ABC):
    """
    Interface for suggesting tailored behavioral interview questions.
    """
    @abstractmethod
    def generate_interview_questions(self, candidate_id: str) -> list:
        pass


class IAIPayrollAuditor(ABC):
    """
    Interface for detecting double payouts or anomalous salary adjustments.
    """
    @abstractmethod
    def audit_payroll(self, period_id: str) -> list:
        pass


class IAIPerformanceCoach(ABC):
    """
    Interface for suggesting employee career development goals.
    """
    @abstractmethod
    def suggest_kpis(self, employee_id: str) -> list:
        pass


class IAITrainingAdvisor(ABC):
    """
    Interface for recommending continuing professional development (CPD) courses.
    """
    @abstractmethod
    def recommend_training(self, employee_id: str) -> list:
        pass


class IAILeavePredictor(ABC):
    """
    Interface for identifying potential absenteeism or seasonal leave spikes.
    """
    @abstractmethod
    def predict_leave_spikes(self, school_id: str) -> dict:
        pass
