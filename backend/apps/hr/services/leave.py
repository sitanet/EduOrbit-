import uuid
from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from backend.apps.hr.models import LeaveType, LeavePolicy, LeaveRequest, LeaveBalance, PublicHoliday, LeaveEncashment, HRAuditLog
from backend.apps.hr.validators import LeaveValidator
from backend.apps.core.events import event_bus, DomainEvent

class LeaveService:
    @staticmethod
    @transaction.atomic
    def submit_leave_request(tenant, employee, leave_type, start_date, end_date, reason="", attachment_url=""):
        LeaveValidator.validate_leave_dates(start_date, end_date)
        
        days_requested = (end_date - start_date).days + 1
        
        # Balance check
        balance, _ = LeaveBalance.objects.get_or_create(
            tenant=tenant,
            employee=employee,
            leave_type=leave_type,
            defaults={
                'leave_type_name': leave_type.name,
                'allowed_days': leave_type.default_days_per_year,
                'remaining_days': leave_type.default_days_per_year
            }
        )
        
        LeaveValidator.validate_leave_balance(balance.remaining_days, days_requested)
        
        req = LeaveRequest.objects.create(
            tenant=tenant,
            employee=employee,
            leave_type=leave_type,
            leave_type_name=leave_type.name,
            start_date=start_date,
            end_date=end_date,
            days_requested=days_requested,
            reason=reason,
            attachment_url=attachment_url,
            status='submitted'
        )
        
        event = DomainEvent("leave.requested", tenant_id=str(tenant.id), data={"id": str(req.id), "employee_id": str(employee.id)})
        transaction.on_commit(lambda: event_bus.publish(event))
        return req

    @staticmethod
    @transaction.atomic
    def approve_leave_request(tenant, leave_request_id, approver_employee=None):
        req = LeaveRequest.objects.get(tenant=tenant, id=leave_request_id)
        if req.status in ['hr_approved', 'completed']:
            return req
            
        req.status = 'hr_approved'
        req.hr_approved_at = timezone.now()
        req.save()
        
        # Deduct balance
        balance = LeaveBalance.objects.filter(tenant=tenant, employee=req.employee, leave_type=req.leave_type).first()
        if balance:
            balance.used_days += req.days_requested
            balance.remaining_days = max(0, balance.allowed_days - balance.used_days)
            balance.save()
            
        # Log Audit Log
        HRAuditLog.objects.create(
            tenant=tenant,
            actor=approver_employee.person if approver_employee else None,
            event_type='leave.approved',
            model_affected='LeaveRequest',
            object_id=str(req.id),
            new_values={'days_deducted': req.days_requested, 'status': 'hr_approved'}
        )
        
        # Publish Domain Event
        event = DomainEvent("leave.approved", tenant_id=str(tenant.id), data={"id": str(req.id), "employee_id": str(req.employee.id)})
        transaction.on_commit(lambda: event_bus.publish(event))
        return req

    @staticmethod
    @transaction.atomic
    def reject_leave_request(tenant, leave_request_id, approver_employee=None, reason=""):
        req = LeaveRequest.objects.get(tenant=tenant, id=leave_request_id)
        req.status = 'rejected'
        req.save()
        
        HRAuditLog.objects.create(
            tenant=tenant,
            actor=approver_employee.person if approver_employee else None,
            event_type='leave.rejected',
            model_affected='LeaveRequest',
            object_id=str(req.id),
            reason=reason
        )
        return req

    @staticmethod
    @transaction.atomic
    def encash_leave(tenant, employee, leave_type, days_to_encash, daily_rate):
        balance = LeaveBalance.objects.filter(tenant=tenant, employee=employee, leave_type=leave_type).first()
        if not balance or balance.remaining_days < days_to_encash:
            raise ValueError("Insufficient remaining leave days for encashment.")
            
        amount = days_to_encash * daily_rate
        encashment = LeaveEncashment.objects.create(
            tenant=tenant,
            employee=employee,
            leave_type=leave_type,
            days_to_encash=days_to_encash,
            amount=amount,
            status='submitted'
        )
        return encashment
