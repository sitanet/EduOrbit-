from rest_framework import serializers
from backend.apps.hr.models import (
    EmployeeProfile, JobOpening, Candidate, LeaveRequest, LeaveBalance, PayrollPeriod, SalaryStructure, PayrollRun, PerformanceReview, TrainingProgram
)

class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeProfile
        fields = ['id', 'person', 'employee_number', 'job_title', 'salary_grade', 'status', 'joined_date']


class JobOpeningSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobOpening
        fields = ['id', 'title', 'description', 'department']


class CandidateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidate
        fields = ['id', 'job_opening', 'first_name', 'last_name', 'email', 'status']


class LeaveRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveRequest
        fields = ['id', 'employee', 'leave_type', 'start_date', 'end_date', 'status', 'reason']


class LeaveBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveBalance
        fields = ['id', 'employee', 'leave_type', 'allowed_days', 'remaining_days']


class PayrollPeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollPeriod
        fields = ['id', 'name', 'start_date', 'end_date', 'status']


class SalaryStructureSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalaryStructure
        fields = ['id', 'grade', 'base_salary']


class PayrollRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollRun
        fields = ['id', 'employee', 'period', 'earnings', 'deductions', 'net_pay', 'status']


class PerformanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerformanceReview
        fields = ['id', 'employee', 'reviewer', 'score', 'review_date', 'remarks']


class TrainingSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingProgram
        fields = ['id', 'name', 'cost', 'cpd_hours']
