from rest_framework import serializers
from backend.apps.people.models import Person
from backend.apps.hr.models import (
    EmployeeProfile, OrgAssignmentHistory, JobRequisition, JobVacancy, JobApplication, InterviewPanel, InterviewScorecard, OfferLetter, OnboardingTask, HRSettings, LeaveType, LeavePolicy, LeaveRequest, LeaveBalance, PublicHoliday, LeaveEncashment, PayrollPeriod, SalaryStructure, PayrollRun, PayrollGLAccount, PayrollAccountingConfiguration, PayrollPayslip, PerformanceReview, TrainingProgram, EmployeeAsset
)

class PersonNestedSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    class Meta:
        model = Person
        fields = ['id', 'first_name', 'last_name', 'email', 'gender', 'date_of_birth', 'nationality', 'state_of_origin']


class OrgAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrgAssignmentHistory
        fields = ['campus_name', 'department_name', 'cost_centre', 'job_position', 'is_active']


class EmployeeSerializer(serializers.ModelSerializer):
    person = PersonNestedSerializer(read_only=True)
    assignment_history = OrgAssignmentSerializer(many=True, read_only=True)

    class Meta:
        model = EmployeeProfile
        fields = [
            'id', 'employee_number', 'person', 'job_title', 'salary_grade', 'status', 'employment_type',
            'confirmation_status', 'joined_date', 'probation_end_date', 'bank_name', 'account_number',
            'account_name', 'sort_code_iban', 'next_of_kin_name', 'next_of_kin_relationship',
            'next_of_kin_phone', 'emergency_contact_phone', 'assignment_history'
        ]


class JobRequisitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobRequisition
        fields = ['id', 'title', 'department', 'number_of_openings', 'reason', 'requested_by', 'status']


class JobVacancySerializer(serializers.ModelSerializer):
    class Meta:
        model = JobVacancy
        fields = ['id', 'requisition', 'title', 'description', 'department', 'status', 'closing_date']


class JobApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobApplication
        fields = ['id', 'vacancy', 'first_name', 'last_name', 'email', 'phone', 'resume_url', 'stage', 'ai_score', 'ai_summary']


class InterviewPanelSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewPanel
        fields = ['id', 'application', 'scheduled_at', 'interview_type', 'location_link']


class InterviewScorecardSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewScorecard
        fields = ['id', 'application', 'interviewer', 'score', 'feedback', 'recommendation']


class OfferLetterSerializer(serializers.ModelSerializer):
    class Meta:
        model = OfferLetter
        fields = ['id', 'application', 'offered_salary', 'designation', 'start_date', 'status']


class OnboardingTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = OnboardingTask
        fields = ['id', 'employee', 'task_name', 'category', 'due_date', 'is_completed', 'completed_at']


class LeaveTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveType
        fields = ['id', 'name', 'code', 'default_days_per_year', 'is_paid', 'requires_document', 'allow_encashment']


class LeaveRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveRequest
        fields = [
            'id', 'employee', 'leave_type', 'leave_type_name', 'start_date', 'end_date',
            'days_requested', 'status', 'reason', 'attachment_url', 'supervisor_approved_at', 'hr_approved_at'
        ]


class LeaveBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveBalance
        fields = ['id', 'employee', 'leave_type', 'leave_type_name', 'allowed_days', 'used_days', 'remaining_days', 'year']


class PublicHolidaySerializer(serializers.ModelSerializer):
    class Meta:
        model = PublicHoliday
        fields = ['id', 'name', 'date', 'is_recurring']


class HRSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = HRSettings
        fields = '__all__'


# Legacy compatibility
class CandidateSerializer(JobApplicationSerializer):
    pass

class JobOpeningSerializer(JobVacancySerializer):
    pass


class PayrollPeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollPeriod
        fields = '__all__'


class PayrollGLAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollGLAccount
        fields = '__all__'


class SalaryStructureSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalaryStructure
        fields = '__all__'


class PayrollAccountingConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollAccountingConfiguration
        fields = '__all__'


class PayrollRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollRun
        fields = '__all__'


class PayrollPayslipSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollPayslip
        fields = '__all__'


from backend.apps.hr.models.attendance import (
    AttendanceShift, EmployeeAttendanceDevice, EmployeeShiftAssignment,
    ShiftCalendar, AttendanceLog, AttendanceRecord, AttendanceAdjustment,
    AttendanceSummary
)

class AttendanceShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceShift
        fields = '__all__'

class EmployeeAttendanceDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeAttendanceDevice
        fields = '__all__'

class EmployeeShiftAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeShiftAssignment
        fields = '__all__'

class ShiftCalendarSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShiftCalendar
        fields = '__all__'

class AttendanceLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceLog
        fields = '__all__'

class AttendanceRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceRecord
        fields = '__all__'

class AttendanceAdjustmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceAdjustment
        fields = '__all__'

class AttendanceSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceSummary
        fields = '__all__'

