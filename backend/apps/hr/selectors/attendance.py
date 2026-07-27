from decimal import Decimal
from dataclasses import dataclass
from datetime import date, datetime
from django.db.models import Sum, Count, Q
from backend.apps.hr.models.attendance import (
    AttendanceRecord, AttendanceShift, AttendanceAdjustment, AttendanceLog
)

@dataclass(frozen=True)
class PayrollAttendanceSummary:
    working_days: int
    paid_days: int
    absent_days: int
    leave_days: int
    holiday_days: int
    weekend_days: int
    late_minutes: int
    overtime_hours: Decimal
    night_shift_hours: Decimal
    public_holiday_hours: Decimal
    approved_adjustment_count: int

class AttendanceSelector:
    @staticmethod
    def get_employee_attendance(employee, start_date, end_date):
        return AttendanceRecord.objects.filter(
            employee=employee,
            attendance_date__range=(start_date, end_date)
        ).order_by('attendance_date')

    @staticmethod
    def get_department_summary(tenant, date):
        records = AttendanceRecord.objects.filter(tenant=tenant, attendance_date=date)
        return {
            'total': records.count(),
            'present': records.filter(attendance_status__in=['Present', 'Late']).count(),
            'late': records.filter(attendance_status='Late').count(),
            'absent': records.filter(attendance_status='Absent').count(),
            'leave': records.filter(attendance_status='Leave').count(),
            'half_day': records.filter(attendance_status='Half Day').count()
        }

    @staticmethod
    def get_shift_summary(tenant, date):
        records = AttendanceRecord.objects.filter(tenant=tenant, attendance_date=date)
        return records.values('shift__name').annotate(
            count=Count('id'),
            present=Count('id', filter=Q(attendance_status__in=['Present', 'Late'])),
            late=Count('id', filter=Q(attendance_status='Late')),
            absent=Count('id', filter=Q(attendance_status='Absent'))
        )

    @staticmethod
    def get_monthly_statistics(employee, year, month):
        records = AttendanceRecord.objects.filter(
            employee=employee,
            attendance_date__year=year,
            attendance_date__month=month
        )
        agg = records.aggregate(
            total_hours=Sum('total_hours'),
            overtime_hours=Sum('overtime_hours'),
            late_minutes=Sum('late_minutes')
        )
        return {
            'total_present': records.filter(attendance_status__in=['Present', 'Late']).count(),
            'total_late': records.filter(attendance_status='Late').count(),
            'total_absent': records.filter(attendance_status='Absent').count(),
            'total_leave': records.filter(attendance_status='Leave').count(),
            'total_hours': agg['total_hours'] or Decimal('0.00'),
            'overtime_hours': agg['overtime_hours'] or Decimal('0.00'),
            'late_minutes': agg['late_minutes'] or 0
        }

    @staticmethod
    def get_overtime(tenant, start_date, end_date):
        return AttendanceRecord.objects.filter(
            tenant=tenant,
            attendance_date__range=(start_date, end_date),
            overtime_hours__gt=0
        ).order_by('-overtime_hours')

    @staticmethod
    def get_absent_staff(tenant, date):
        return AttendanceRecord.objects.filter(
            tenant=tenant,
            attendance_date=date,
            attendance_status='Absent'
        )

    @staticmethod
    def get_late_staff(tenant, date):
        return AttendanceRecord.objects.filter(
            tenant=tenant,
            attendance_date=date,
            attendance_status='Late'
        )

    @staticmethod
    def get_payroll_attendance_summary(employee, start_date, end_date) -> PayrollAttendanceSummary:
        records = AttendanceRecord.objects.filter(
            employee=employee,
            attendance_date__range=(start_date, end_date)
        )
        
        working_days = records.filter(attendance_status__in=['Present', 'Late', 'Remote', 'Half Day']).count()
        absent_days = records.filter(attendance_status='Absent').count()
        leave_days = records.filter(attendance_status='Leave').count()
        holiday_days = records.filter(attendance_status='Holiday').count()
        weekend_days = records.filter(attendance_status='Weekend').count()
        
        # Paid days = working days + leave days + holiday days
        paid_days = working_days + leave_days + holiday_days
        
        agg = records.aggregate(
            total_late_minutes=Sum('late_minutes'),
            total_overtime=Sum('overtime_hours')
        )
        
        # Calculate public holiday hours and night shift hours if applicable
        # For simplicity, public holiday hours = total hours worked on a Holiday status record
        public_holiday_hours = records.filter(attendance_status='Holiday').aggregate(
            h=Sum('total_hours')
        )['h'] or Decimal('0.00')
        
        # Night shift hours = total hours worked on overnight shifts
        night_shift_hours = records.filter(shift__overnight_shift=True).aggregate(
            h=Sum('total_hours')
        )['h'] or Decimal('0.00')
        
        # Approved adjustments count
        adjustments_count = AttendanceAdjustment.objects.filter(
            attendance_record__employee=employee,
            attendance_record__attendance_date__range=(start_date, end_date),
            approval_status='HR Approved'
        ).count()

        return PayrollAttendanceSummary(
            working_days=working_days,
            paid_days=paid_days,
            absent_days=absent_days,
            leave_days=leave_days,
            holiday_days=holiday_days,
            weekend_days=weekend_days,
            late_minutes=agg['total_late_minutes'] or 0,
            overtime_hours=agg['total_overtime'] or Decimal('0.00'),
            night_shift_hours=night_shift_hours,
            public_holiday_hours=public_holiday_hours,
            approved_adjustment_count=adjustments_count
        )
