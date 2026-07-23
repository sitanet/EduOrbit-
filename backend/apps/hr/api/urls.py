from django.urls import path
from backend.apps.hr.api.views import (
    EmployeeProfileAPIView, LeaveRequestAPIView, PayrollRunAPIView
)

app_name = 'hr_api'

urlpatterns = [
    path('employees/', EmployeeProfileAPIView.as_view(), name='employees'),
    path('leave/', LeaveRequestAPIView.as_view(), name='leave'),
    path('payroll/', PayrollRunAPIView.as_view(), name='payroll'),
]
