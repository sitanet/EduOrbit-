from django.urls import path, include
from backend.apps.hr.views_web import (
    HRDashboardWebView, LeaveCalendarWebView, RecruitmentDashboardWebView, CandidateReviewWebView, PayrollWebView,
    AttendanceDashboardWebView, AttendanceGenerateWebView, AttendanceAdjustmentActionWebView, AttendanceReportWebView,
    ESSDashboardWebView, ManagerTeamWebView, StaffDirectoryWebView, OrgChartWebView, OnboardingTrackerWebView,
    PerformanceWebView, TrainingWebView, DisciplinaryWebView, RewardsWebView, FinancePostingsWebView,
    AnalyticsWebView, NotificationsWebView, AuditTrailWebView, HRSettingsWebView, ImportWizardWebView,
    BulkOperationsWebView, EnterpriseSearchWebView, ReportsHubWebView, HRUserManualWebView, OnboardingWizardWebView
)

urlpatterns = [
    # Portals & Core Web Views
    path('dashboard/', HRDashboardWebView.as_view(), name='hr_dashboard_web'),
    path('ess/', ESSDashboardWebView.as_view(), name='hr_ess_dashboard'),
    path('manager/team/', ManagerTeamWebView.as_view(), name='hr_manager_team'),
    path('admin/dashboard/', HRDashboardWebView.as_view(), name='hr_admin_dashboard'),
    path('admin/directory/', StaffDirectoryWebView.as_view(), name='hr_admin_directory'),
    path('admin/org-chart/', OrgChartWebView.as_view(), name='hr_admin_org_chart'),
    path('admin/onboarding/', RecruitmentDashboardWebView.as_view(), name='hr_admin_onboarding'),
    path('admin/onboarding/wizard/', OnboardingWizardWebView.as_view(), name='hr_admin_onboarding_wizard'),

    # Recruitment & Leave
    path('recruitment/', RecruitmentDashboardWebView.as_view(), name='recruitment_dashboard_web'),
    path('recruitment/candidate/<uuid:candidate_id>/review/', CandidateReviewWebView.as_view(), name='candidate_review_web'),
    path('leave-calendar/', LeaveCalendarWebView.as_view(), name='leave_calendar_web'),

    # Attendance
    path('attendance/', AttendanceDashboardWebView.as_view(), name='hr_attendance_dashboard'),
    path('attendance/generate/', AttendanceGenerateWebView.as_view(), name='hr_attendance_generate'),
    path('attendance/adjustment/<uuid:adjustment_id>/approve/', AttendanceAdjustmentActionWebView.as_view(), {'action': 'approve'}, name='hr_attendance_approve_adjustment'),
    path('attendance/adjustment/<uuid:adjustment_id>/reject/', AttendanceAdjustmentActionWebView.as_view(), {'action': 'reject'}, name='hr_attendance_reject_adjustment'),
    path('attendance/report/', AttendanceReportWebView.as_view(), name='hr_attendance_report'),

    # Payroll & Finance
    path('payroll/', PayrollWebView.as_view(), name='payroll_dashboard_web'),
    path('payroll/generate/', PayrollWebView.as_view(), name='payroll-generate'),
    path('payroll/post/<uuid:run_id>/', PayrollWebView.as_view(), name='payroll-post'),
    path('finance/postings/', FinancePostingsWebView.as_view(), name='hr_finance_postings'),

    # Modules
    path('performance/', PerformanceWebView.as_view(), name='hr_performance'),
    path('training/', TrainingWebView.as_view(), name='hr_training'),
    path('disciplinary/', DisciplinaryWebView.as_view(), name='hr_disciplinary'),
    path('rewards/', RewardsWebView.as_view(), name='hr_rewards'),

    # Analytics, Audit & Search
    path('analytics/', AnalyticsWebView.as_view(), name='hr_analytics'),
    path('notifications/', NotificationsWebView.as_view(), name='hr_notifications'),
    path('audit/', AuditTrailWebView.as_view(), name='hr_audit_trail'),
    path('settings/', HRSettingsWebView.as_view(), name='hr_settings'),
    path('import/', ImportWizardWebView.as_view(), name='hr_import_wizard'),
    path('bulk/', BulkOperationsWebView.as_view(), name='hr_bulk_operations'),
    path('search/', EnterpriseSearchWebView.as_view(), name='hr_search'),
    path('reports/', ReportsHubWebView.as_view(), name='hr_reports_hub'),
    path('manual/', HRUserManualWebView.as_view(), name='hr_user_manual_web'),
    path('user-manual/', HRUserManualWebView.as_view(), name='hr_user_manual_alt'),
    path('admin/manual/', HRUserManualWebView.as_view(), name='hr_admin_manual'),
    
    # API endpoints versions
    path('api/v1/', include('backend.apps.hr.api.urls')),
]
