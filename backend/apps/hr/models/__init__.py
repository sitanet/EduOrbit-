from .settings import HRSettings
from .employee import EmployeeProfile, OrgAssignmentHistory, HRAuditLog
from .position import JobPosition
from .compensation import CompensationHistory, ContractHistory
from .workflow import ApprovalWorkflow
from .onboarding_draft import OnboardingDraft
from .recruitment import (
    JobRequisition, JobVacancy, JobApplication, InterviewPanel, InterviewScorecard, OfferLetter, TalentPool
)
from .onboarding import OnboardingChecklist, OnboardingTask
from .leave import LeaveType, LeavePolicy, LeaveRequest, LeaveBalance, PublicHoliday, LeaveEncashment
from .payroll import PayrollPeriod, SalaryStructure, PayrollRun, PayrollGLAccount, PayrollAccountingConfiguration, PayrollPayslip
from .appraisal import PerformanceReview, PerformanceObjective
from .training import TrainingProgram
from .assets import EmployeeAsset

# Backward compatibility alias
Candidate = JobApplication
JobOpening = JobVacancy
Interview = InterviewPanel

__all__ = [
    'HRSettings',
    'EmployeeProfile',
    'OrgAssignmentHistory',
    'HRAuditLog',
    'JobRequisition',
    'JobVacancy',
    'JobOpening',
    'JobApplication',
    'Candidate',
    'InterviewPanel',
    'Interview',
    'InterviewScorecard',
    'OfferLetter',
    'TalentPool',
    'OnboardingChecklist',
    'OnboardingTask',
    'LeaveType',
    'LeavePolicy',
    'LeaveRequest',
    'LeaveBalance',
    'PublicHoliday',
    'LeaveEncashment',
    'PayrollPeriod',
    'SalaryStructure',
    'PayrollRun',
    'PayrollGLAccount',
    'PayrollAccountingConfiguration',
    'PayrollPayslip',
    'PerformanceReview',
    'PerformanceObjective',
    'TrainingProgram',
    'EmployeeAsset',
    'AttendanceShift',
    'EmployeeAttendanceDevice',
    'EmployeeShiftAssignment',
    'ShiftCalendar',
    'AttendanceLog',
    'AttendanceRecord',
    'AttendanceAdjustment',
    'AttendanceSummary',
]

from .attendance import (
    AttendanceShift, EmployeeAttendanceDevice, EmployeeShiftAssignment,
    ShiftCalendar, AttendanceLog, AttendanceRecord, AttendanceAdjustment,
    AttendanceSummary
)
