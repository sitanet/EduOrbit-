# Guard against double-import via wrong path during Django test runner discovery.
# Django's test runner walks all packages in the apps/ directory recursively.
# When it imports this package as 'apps.hr.models' (wrong path), we skip all
# model imports to prevent a RuntimeError conflict with the already-registered
# 'backend.apps.hr.models' models.
if __name__ == 'backend.apps.hr.models':
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
    from .attendance import (
        AttendanceShift, EmployeeAttendanceDevice, EmployeeShiftAssignment,
        ShiftCalendar, AttendanceLog, AttendanceRecord, AttendanceAdjustment,
        AttendanceSummary
    )

    # Backward compatibility aliases
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

