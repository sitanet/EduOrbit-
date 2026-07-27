from django.urls import path
from backend.apps.dashboard.views_web import (
    DashboardDispatchView,
    SuperAdminDashboardView,
    SchoolAdminDashboardView,
    TeacherDashboardView,
    StudentDashboardView,
    ParentDashboardView,
    FinanceDashboardView,
    HRDashboardView,
    LibraryDashboardView,
    HostelDashboardView,
    TransportDashboardView,
    ClinicDashboardView,
    ExamDashboardView,
)

urlpatterns = [
    # ── Central dispatcher (resolve and redirect) ────────────────────────────
    path('', DashboardDispatchView.as_view(), name='dashboard_home'),

    # ── Role-isolated dashboard routes ───────────────────────────────────────
    path('super-admin/',  SuperAdminDashboardView.as_view(),  name='dashboard_super_admin'),
    path('school-admin/', SchoolAdminDashboardView.as_view(), name='dashboard_school_admin'),
    path('teacher/',      TeacherDashboardView.as_view(),     name='dashboard_teacher'),
    path('student/',      StudentDashboardView.as_view(),     name='dashboard_student'),
    path('parent/',       ParentDashboardView.as_view(),      name='dashboard_parent'),
    path('finance/',      FinanceDashboardView.as_view(),     name='dashboard_finance'),
    path('hr/',           HRDashboardView.as_view(),          name='dashboard_hr'),
    path('library/',      LibraryDashboardView.as_view(),     name='dashboard_library'),
    path('hostel/',       HostelDashboardView.as_view(),      name='dashboard_hostel'),
    path('transport/',    TransportDashboardView.as_view(),   name='dashboard_transport'),
    path('clinic/',       ClinicDashboardView.as_view(),      name='dashboard_clinic'),
    path('exam/',         ExamDashboardView.as_view(),        name='dashboard_exam'),
]
