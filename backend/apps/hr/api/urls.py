from django.urls import path, include
from rest_framework.routers import DefaultRouter
from backend.apps.hr.api.views import (
    EmployeeViewSet, JobVacancyViewSet, JobApplicationViewSet, OnboardingTaskViewSet, HRSettingsViewSet, LeaveRequestViewSet,
    PayrollPeriodViewSet, PayrollGLAccountViewSet, SalaryStructureViewSet, PayrollAccountingConfigurationViewSet, PayrollRunViewSet, PayrollPayslipViewSet,
    AttendanceShiftViewSet, AttendanceRecordViewSet, AttendanceAdjustmentViewSet, PublicHolidayViewSet, AttendanceDashboardViewSet
)

from backend.apps.hr.api.kyc_views import (
    VerifyNINAPIView, VerifyBVNAPIView, ResolveBankAccountAPIView, AutoSaveDraftAPIView, SubmitOnboardingAPIView,
    ReplaceEmployeePhotoAPIView, ProtectedEmployeePhotoView
)

router = DefaultRouter()
router.register(r'employees', EmployeeViewSet, basename='hr-employees')
router.register(r'recruitment/vacancies', JobVacancyViewSet, basename='hr-vacancies')
router.register(r'recruitment/applications', JobApplicationViewSet, basename='hr-applications')
router.register(r'onboarding', OnboardingTaskViewSet, basename='hr-onboarding')
router.register(r'leave', LeaveRequestViewSet, basename='hr-leave')
router.register(r'settings', HRSettingsViewSet, basename='hr-settings')
router.register(r'payroll/periods', PayrollPeriodViewSet, basename='hr-payroll-periods')
router.register(r'payroll/gl-accounts', PayrollGLAccountViewSet, basename='hr-payroll-gl-accounts')
router.register(r'payroll/salary-structures', SalaryStructureViewSet, basename='hr-payroll-salary-structures')
router.register(r'payroll/accounting-configs', PayrollAccountingConfigurationViewSet, basename='hr-payroll-accounting-configs')
router.register(r'payroll/runs', PayrollRunViewSet, basename='hr-payroll-runs')
router.register(r'payroll/payslips', PayrollPayslipViewSet, basename='hr-payroll-payslips')
router.register(r'attendance/shifts', AttendanceShiftViewSet, basename='hr-attendance-shifts')
router.register(r'attendance/records', AttendanceRecordViewSet, basename='hr-attendance-records')
router.register(r'attendance/adjustments', AttendanceAdjustmentViewSet, basename='hr-attendance-adjustments')
router.register(r'attendance/holidays', PublicHolidayViewSet, basename='hr-attendance-holidays')
router.register(r'attendance/dashboard', AttendanceDashboardViewSet, basename='hr-attendance-dashboard')

urlpatterns = [
    path('', include(router.urls)),
    path('kyc/verify-nin/', VerifyNINAPIView.as_view(), name='hr_kyc_verify_nin'),
    path('kyc/verify-bvn/', VerifyBVNAPIView.as_view(), name='hr_kyc_verify_bvn'),
    path('kyc/resolve-bank/', ResolveBankAccountAPIView.as_view(), name='hr_kyc_resolve_bank'),
    path('onboarding/draft/auto-save/', AutoSaveDraftAPIView.as_view(), name='hr_onboarding_auto_save'),
    path('onboarding/submit/', SubmitOnboardingAPIView.as_view(), name='hr_onboarding_submit'),
    path('employees/<uuid:employee_id>/replace-photo/', ReplaceEmployeePhotoAPIView.as_view(), name='hr_employee_replace_photo'),
    path('employees/<uuid:employee_id>/photo/', ProtectedEmployeePhotoView.as_view(), name='hr_employee_protected_photo'),
]
