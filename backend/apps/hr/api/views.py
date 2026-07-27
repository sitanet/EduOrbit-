from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from backend.apps.hr.models import (
    EmployeeProfile, JobVacancy, JobApplication, OnboardingTask, HRSettings, LeaveRequest, LeaveType, LeaveBalance, PublicHoliday,
    PayrollPeriod, PayrollGLAccount, SalaryStructure, PayrollAccountingConfiguration, PayrollRun, PayrollPayslip
)
from backend.apps.hr.api.serializers import (
    EmployeeSerializer, JobVacancySerializer, JobApplicationSerializer, OnboardingTaskSerializer, HRSettingsSerializer, LeaveRequestSerializer, LeaveTypeSerializer, LeaveBalanceSerializer, PublicHolidaySerializer,
    PayrollPeriodSerializer, PayrollGLAccountSerializer, SalaryStructureSerializer, PayrollAccountingConfigurationSerializer, PayrollRunSerializer, PayrollPayslipSerializer
)
from backend.apps.hr.selectors import EmployeeSelector, RecruitmentSelector, OnboardingSelector, HRSettingsSelector, LeaveSelector
from backend.apps.hr.services import EmployeeService, RecruitmentService, OnboardingService, LeaveService, PayrollService
from backend.apps.efbm.services.finance import AccountingService
from backend.apps.hr.permissions import IsHRAdmin

class EmployeeViewSet(viewsets.ModelViewSet):
    serializer_class = EmployeeSerializer
    permission_classes = [IsHRAdmin]
    filterset_fields = ['status', 'employment_type', 'confirmation_status']
    search_fields = ['employee_number', 'person__first_name', 'person__last_name', 'person__user__email', 'job_title']
    ordering_fields = ['joined_date', 'employee_number', 'created_at']

    def get_queryset(self):
        filters = {}
        if self.request.query_params.get('search'):
            filters['search'] = self.request.query_params.get('search')
        if self.request.query_params.get('status'):
            filters['status'] = self.request.query_params.get('status')
        if self.request.query_params.get('department'):
            filters['department'] = self.request.query_params.get('department')
        return EmployeeSelector.get_all_employees(self.request.tenant, filters=filters)

    def create(self, request, *args, **kwargs):
        data = request.data
        employee = EmployeeService.create_employee(
            tenant=request.tenant,
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            email=data.get('email'),
            job_title=data.get('job_title', 'Support Staff'),
            salary_grade=data.get('salary_grade', 'grade_1'),
            employment_type=data.get('employment_type', 'full_time'),
            department_name=data.get('department_name', 'Academics')
        )
        serializer = self.get_serializer(employee)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class JobVacancyViewSet(viewsets.ModelViewSet):
    serializer_class = JobVacancySerializer
    permission_classes = [IsHRAdmin]

    def get_queryset(self):
        return RecruitmentSelector.get_vacancies(self.request.tenant)


class JobApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = JobApplicationSerializer
    permission_classes = [IsHRAdmin]

    def get_queryset(self):
        return RecruitmentSelector.get_applications(self.request.tenant)

    @action(detail=True, methods=['post'])
    def hire(self, request, pk=None):
        app = self.get_object()
        employee = RecruitmentService.hire_candidate(request.tenant, app)
        return Response({'success': True, 'employee_id': str(employee.id)}, status=status.HTTP_200_OK)


class OnboardingTaskViewSet(viewsets.ModelViewSet):
    serializer_class = OnboardingTaskSerializer
    permission_classes = [IsHRAdmin]

    def get_queryset(self):
        employee_id = self.request.query_params.get('employee_id')
        if employee_id:
            return OnboardingSelector.get_tasks_for_employee(self.request.tenant, employee_id)
        return OnboardingTask.objects.filter(tenant=self.request.tenant)


class LeaveRequestViewSet(viewsets.ModelViewSet):
    serializer_class = LeaveRequestSerializer
    permission_classes = [IsHRAdmin]

    def get_queryset(self):
        employee_id = self.request.query_params.get('employee_id')
        req_status = self.request.query_params.get('status')
        return LeaveSelector.get_leave_requests(self.request.tenant, employee_id=employee_id, status=req_status)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        leave_req = LeaveService.approve_leave_request(request.tenant, pk)
        return Response({'success': True, 'status': leave_req.status}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        reason = request.data.get('reason', '')
        leave_req = LeaveService.reject_leave_request(request.tenant, pk, reason=reason)
        return Response({'success': True, 'status': leave_req.status}, status=status.HTTP_200_OK)


class HRSettingsViewSet(viewsets.ModelViewSet):
    serializer_class = HRSettingsSerializer
    permission_classes = [IsHRAdmin]

    def get_queryset(self):
        return HRSettings.objects.filter(tenant=self.request.tenant)


class PayrollPeriodViewSet(viewsets.ModelViewSet):
    serializer_class = PayrollPeriodSerializer
    permission_classes = [IsHRAdmin]

    def get_queryset(self):
        return PayrollPeriod.objects.filter(tenant=self.request.tenant)


class PayrollGLAccountViewSet(viewsets.ModelViewSet):
    serializer_class = PayrollGLAccountSerializer
    permission_classes = [IsHRAdmin]

    def get_queryset(self):
        return PayrollGLAccount.objects.filter(tenant=self.request.tenant)


class SalaryStructureViewSet(viewsets.ModelViewSet):
    serializer_class = SalaryStructureSerializer
    permission_classes = [IsHRAdmin]

    def get_queryset(self):
        return SalaryStructure.objects.filter(tenant=self.request.tenant)


class PayrollAccountingConfigurationViewSet(viewsets.ModelViewSet):
    serializer_class = PayrollAccountingConfigurationSerializer
    permission_classes = [IsHRAdmin]

    def get_queryset(self):
        return PayrollAccountingConfiguration.objects.filter(tenant=self.request.tenant)


class PayrollRunViewSet(viewsets.ModelViewSet):
    serializer_class = PayrollRunSerializer
    permission_classes = [IsHRAdmin]

    def get_queryset(self):
        return PayrollRun.objects.filter(tenant=self.request.tenant)

    @action(detail=False, methods=['post'])
    def generate(self, request):
        period_id = request.data.get('period_id')
        if not period_id:
            return Response({'error': 'Missing period_id'}, status=status.HTTP_400_BAD_REQUEST)
        
        run = PayrollService.generate_payroll_run(request.tenant, period_id)
        return Response({'success': True, 'payroll_run_id': run.id, 'status': run.status}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def approve_and_post(self, request, pk=None):
        accounting_service = AccountingService()
        run = PayrollService.approve_and_post_payroll(request.tenant, pk, accounting_service)
        return Response({'success': True, 'status': run.status}, status=status.HTTP_200_OK)


class PayrollPayslipViewSet(viewsets.ModelViewSet):
    serializer_class = PayrollPayslipSerializer
    permission_classes = [IsHRAdmin]

    def get_queryset(self):
        payroll_run_id = self.request.query_params.get('payroll_run_id')
        qs = PayrollPayslip.objects.filter(tenant=self.request.tenant)
        if payroll_run_id:
            qs = qs.filter(payroll_run_id=payroll_run_id)
        return qs


from backend.apps.hr.models.attendance import (
    AttendanceShift, EmployeeAttendanceDevice, EmployeeShiftAssignment,
    ShiftCalendar, AttendanceLog, AttendanceRecord, AttendanceAdjustment,
    AttendanceSummary
)
from backend.apps.hr.models.leave import PublicHoliday
from backend.apps.hr.api.serializers import (
    AttendanceShiftSerializer, EmployeeAttendanceDeviceSerializer,
    EmployeeShiftAssignmentSerializer, ShiftCalendarSerializer,
    AttendanceLogSerializer, AttendanceRecordSerializer,
    AttendanceAdjustmentSerializer, AttendanceSummarySerializer
)

class AttendanceShiftViewSet(viewsets.ModelViewSet):
    serializer_class = AttendanceShiftSerializer
    permission_classes = [IsHRAdmin]

    def get_queryset(self):
        return AttendanceShift.objects.filter(tenant=self.request.tenant)


class AttendanceRecordViewSet(viewsets.ModelViewSet):
    serializer_class = AttendanceRecordSerializer
    permission_classes = [IsHRAdmin]

    def get_queryset(self):
        tenant = self.request.tenant
        qs = AttendanceRecord.objects.filter(tenant=tenant)
        
        # Filtering parameters
        employee_id = self.request.query_params.get('employee')
        date_val = self.request.query_params.get('date')
        status = self.request.query_params.get('status')
        shift_id = self.request.query_params.get('shift')
        
        if employee_id:
            qs = qs.filter(employee_id=employee_id)
        if date_val:
            qs = qs.filter(attendance_date=date_val)
        if status:
            qs = qs.filter(attendance_status=status)
        if shift_id:
            qs = qs.filter(shift_id=shift_id)
            
        return qs


class AttendanceAdjustmentViewSet(viewsets.ModelViewSet):
    serializer_class = AttendanceAdjustmentSerializer
    permission_classes = [IsHRAdmin]

    def get_queryset(self):
        return AttendanceAdjustment.objects.filter(tenant=self.request.tenant)


class PublicHolidayViewSet(viewsets.ModelViewSet):
    permission_classes = [IsHRAdmin]

    def get_serializer_class(self):
        from backend.apps.hr.api.serializers import PublicHolidaySerializer
        return PublicHolidaySerializer

    def get_queryset(self):
        return PublicHoliday.objects.filter(tenant=self.request.tenant)


class AttendanceDashboardViewSet(viewsets.ViewSet):
    permission_classes = [IsHRAdmin]

    def list(self, request):
        from backend.apps.hr.selectors.attendance import AttendanceSelector
        tenant = request.tenant
        target_date = request.query_params.get('date', timezone.now().date().isoformat())
        
        summary = AttendanceSelector.get_department_summary(tenant, target_date)
        late_staff = AttendanceSelector.get_late_staff(tenant, target_date)
        absent_staff = AttendanceSelector.get_absent_staff(tenant, target_date)
        
        return Response({
            'date': target_date,
            'summary': summary,
            'late_staff_count': late_staff.count(),
            'absent_staff_count': absent_staff.count()
        })

