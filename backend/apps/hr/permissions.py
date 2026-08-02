"""
8-Tier RBAC Permissions for HRPM Module.
"""
from rest_framework.permissions import BasePermission

class IsHRAdmin(BasePermission):
    """
    Grants permission to HR Managers, HR Directors, School Admins, and Superusers.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser or getattr(request.user, 'is_staff', False):
            return True
        return getattr(request, 'hr_role', '') in ['hr_admin', 'hr_officer', 'school_admin', 'super_admin']


class IsPayrollAdmin(BasePermission):
    """
    Grants permission to Payroll Admins and HR Admins.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser or getattr(request.user, 'is_staff', False):
            return True
        return getattr(request, 'hr_role', '') in ['payroll_admin', 'hr_admin', 'super_admin']


class IsHROfficer(BasePermission):
    """
    Grants permission to HR Officers, HR Admins, and Payroll Admins.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser or getattr(request.user, 'is_staff', False):
            return True
        return getattr(request, 'hr_role', '') in ['hr_officer', 'hr_admin', 'payroll_admin', 'super_admin']


class IsSupervisor(BasePermission):
    """
    Grants permission to Supervisors, Managers, and HR Admins.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser or getattr(request.user, 'is_staff', False):
            return True
        return getattr(request, 'is_supervisor', False) or getattr(request, 'hr_role', '') in ['supervisor', 'hr_admin', 'hr_officer', 'super_admin']


class IsFinanceViewer(BasePermission):
    """
    Grants permission to Finance Officers and Payroll Admins to view payroll GL postings.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser or getattr(request.user, 'is_staff', False):
            return True
        return getattr(request, 'hr_role', '') in ['finance', 'payroll_admin', 'hr_admin', 'super_admin']


class CanApproveLeave(BasePermission):
    """
    Grants permission to approve leave requests.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return getattr(request, 'is_supervisor', False) or getattr(request, 'hr_role', '') in ['hr_admin', 'hr_officer', 'super_admin']


class CanApproveAttendance(BasePermission):
    """
    Grants permission to approve attendance adjustments.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return getattr(request, 'is_supervisor', False) or getattr(request, 'hr_role', '') in ['hr_admin', 'hr_officer', 'super_admin']


class IsEmployeeSelf(BasePermission):
    """
    Allows staff members to view or edit their own profile/records.
    """
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        if hasattr(obj, 'person') and obj.person and obj.person.user:
            return obj.person.user == request.user
        if hasattr(obj, 'employee') and obj.employee.person and obj.employee.person.user:
            return obj.employee.person.user == request.user
        return False
