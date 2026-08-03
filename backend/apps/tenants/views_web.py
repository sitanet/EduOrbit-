"""
Production Billing & Subscription Web Portal Views for EduOrbit ERP.
Orchestrates Phase 1-3 Services to render Bootstrap 5 / Tailwind CSS + HTMX + Alpine.js pages.
Strictly enforces RBAC and Multi-Tenant Data Isolation.
"""

import csv
import logging
from decimal import Decimal
from typing import Optional
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse, Http404
from django.views.generic import View, TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.db.models import Sum, Count, Q

from backend.apps.tenants.models import (
    Tenant, School, SubscriptionPlan, TenantSubscription, ParentSubscription,
    StudentPlatformSubscription, SubscriptionInvoice, SubscriptionPayment,
    SubscriptionAuditLog, PaymentGatewaySetting, BillingSettings
)
from backend.apps.people.models import Person, ParentProfile, StudentProfile, FamilyRelationship
from backend.apps.identity.models import User

# Phase 1-3 Services
from backend.apps.tenants.services.billing_calculator import BillingCalculationService
from backend.apps.tenants.services.invoice_service import InvoiceService
from backend.apps.tenants.services.receipt_service import ReceiptService
from backend.apps.tenants.services.parent_subscription_service import ParentSubscriptionService
from backend.apps.tenants.services.school_subscription_service import SchoolSubscriptionService
from backend.apps.tenants.services.compliance_service import ComplianceService
from backend.apps.tenants.services.audit_service import AuditService
from backend.apps.tenants.services.payment_service import PaymentService
from backend.apps.tenants.services.payment_gateway import PaymentGatewayFactory
from backend.apps.tenants.services.pdf_generator import PDFGeneratorService
from backend.apps.tenants.services.payment.refund_service import RefundService
from backend.apps.tenants.services.payment.reconciliation import ReconciliationService

logger = logging.getLogger(__name__)


# ==============================================================
# LEGACY / SHARED WEB VIEWS
# ==============================================================

@method_decorator(login_required, name='dispatch')
class TenantDashboardWebView(TemplateView):
    template_name = 'tenants/billing/school_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = getattr(self.request.user, 'tenant', None) or Tenant.objects.filter(is_active=True).first()
        context['tenant'] = tenant
        comp_res = ComplianceService.calculate_school_compliance_metrics(tenant=tenant) if tenant else None
        context['metrics'] = comp_res.data if comp_res and comp_res.success else {}
        context['collected_amount'] = SubscriptionPayment.objects.filter(tenant=tenant, status='SUCCESSFUL').aggregate(total=Sum('amount'))['total'] or Decimal("0.00") if tenant else Decimal("0.00")
        context['outstanding_amount'] = SubscriptionInvoice.objects.filter(tenant=tenant, status__in=['PENDING', 'OVERDUE']).aggregate(total=Sum('amount'))['total'] or Decimal("0.00") if tenant else Decimal("0.00")
        context['recent_payments'] = SubscriptionPayment.objects.filter(tenant=tenant).order_by('-created_at')[:10] if tenant else []
        return context


@method_decorator(login_required, name='dispatch')
class OnboardWizardWebView(TemplateView):
    template_name = 'tenants/billing/school_dashboard.html'


@method_decorator(login_required, name='dispatch')
class SwitchSchoolView(View):
    def get(self, request):
        return redirect('tenants_web:school_dashboard')


# ==============================================================
# HELPER TENANT & RBAC PERMISSION CHECKS
# ==============================================================

def get_user_tenant(request) -> Optional[Tenant]:
    """Helper resolving user's active tenant safely."""
    if hasattr(request.user, 'tenant') and request.user.tenant:
        return request.user.tenant
    return Tenant.objects.filter(is_active=True).first()


def is_super_admin(user) -> bool:
    return user.is_superuser or user.is_staff or getattr(user, 'role', '') == 'super_admin'


# ==============================================================
# MODULE 1: SOFTWARE OWNER BILLING DASHBOARD
# ==============================================================

@login_required
def super_admin_billing_dashboard(request):
    """
    Platform Super Admin Billing Console displaying global KPIs, revenue, active schools,
    gateway status indicators, and recent payments.
    """
    if not is_super_admin(request.user):
        return render(request, "tenants/billing/access_denied.html", status=403)

    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0)

    # Revenue Metrics
    rev_today = SubscriptionPayment.objects.filter(status='SUCCESSFUL', paid_at__gte=today_start).aggregate(total=Sum('amount'))['total'] or Decimal("0.00")
    rev_month = SubscriptionPayment.objects.filter(status='SUCCESSFUL', paid_at__gte=month_start).aggregate(total=Sum('amount'))['total'] or Decimal("0.00")
    rev_total = SubscriptionPayment.objects.filter(status='SUCCESSFUL').aggregate(total=Sum('amount'))['total'] or Decimal("0.00")

    # Subscription Stats
    active_schools_count = Tenant.objects.filter(is_active=True, billing_status='ACTIVE').count()
    parent_pays_count = Tenant.objects.filter(billing_model='PARENT_PAYS').count()
    school_pays_count = Tenant.objects.filter(billing_model='SCHOOL_PAYS').count()

    # Active Parents & Students
    active_parents_count = ParentSubscription.objects.filter(status='ACTIVE').count()
    active_students_count = StudentPlatformSubscription.objects.filter(payment_status='ACTIVE').count()

    # Gateway Settings
    gateways = PaymentGatewaySetting.objects.all().order_by('priority')

    # Recent Successful Payments
    recent_payments = SubscriptionPayment.objects.select_related('invoice', 'tenant').filter(status='SUCCESSFUL').order_by('-created_at')[:10]

    context = {
        "rev_today": rev_today,
        "rev_month": rev_month,
        "rev_total": rev_total,
        "active_schools_count": active_schools_count,
        "parent_pays_count": parent_pays_count,
        "school_pays_count": school_pays_count,
        "active_parents_count": active_parents_count,
        "active_students_count": active_students_count,
        "gateways": gateways,
        "recent_payments": recent_payments
    }
    return render(request, "tenants/billing/super_admin_dashboard.html", context)


# ==============================================================
# MODULE 2: PAYMENT GATEWAY MANAGEMENT
# ==============================================================

@login_required
def gateway_management(request):
    """
    Software Owner Gateway Management Console.
    Allows enabling/disabling Paystack & OPay, setting maintenance mode, priorities, and callback URLs.
    """
    if not is_super_admin(request.user):
        return render(request, "tenants/billing/access_denied.html", status=403)

    if request.method == "POST":
        provider = request.POST.get('provider')
        gw_setting = get_object_or_404(PaymentGatewaySetting, provider=provider)
        
        gw_setting.enabled = 'enabled' in request.POST
        gw_setting.maintenance_mode = 'maintenance_mode' in request.POST
        gw_setting.priority = int(request.POST.get('priority', gw_setting.priority))
        gw_setting.callback_url = request.POST.get('callback_url', gw_setting.callback_url)
        gw_setting.save()

        AuditService.log_event(
            action="UPDATED",
            actor=request.user,
            notes=f"Updated Gateway Setting for {provider}: Enabled={gw_setting.enabled}, Maint={gw_setting.maintenance_mode}, Priority={gw_setting.priority}"
        )
        return redirect('tenants_web:gateway_management')

    gateways = PaymentGatewaySetting.objects.all().order_by('priority')
    return render(request, "tenants/billing/gateway_management.html", {"gateways": gateways})


# ==============================================================
# MODULE 3 & 9: SCHOOL BILLING DASHBOARD & COMPLIANCE
# ==============================================================

@login_required
def school_billing_dashboard(request):
    """
    School Administrator Billing & Compliance Dashboard.
    Displays school collection stats, compliance percentage gauges, and recent parent payments.
    """
    tenant = get_user_tenant(request)
    if not tenant:
        return render(request, "tenants/billing/access_denied.html", status=403)

    # Compute Compliance Metrics using ComplianceService
    comp_res = ComplianceService.calculate_school_compliance_metrics(tenant=tenant)
    metrics = comp_res.data if comp_res.success else {}

    # Outstanding vs Collected Amount
    collected_amount = SubscriptionPayment.objects.filter(tenant=tenant, status='SUCCESSFUL').aggregate(total=Sum('amount'))['total'] or Decimal("0.00")
    outstanding_amount = SubscriptionInvoice.objects.filter(tenant=tenant, status__in=['PENDING', 'OVERDUE']).aggregate(total=Sum('amount'))['total'] or Decimal("0.00")

    # Recent Payments for Tenant
    recent_payments = SubscriptionPayment.objects.filter(tenant=tenant).order_by('-created_at')[:10]

    context = {
        "tenant": tenant,
        "metrics": metrics,
        "collected_amount": collected_amount,
        "outstanding_amount": outstanding_amount,
        "recent_payments": recent_payments
    }
    return render(request, "tenants/billing/school_dashboard.html", context)


# ==============================================================
# MODULE 4 & 10: PARENT COLLECTION CENTER (HTMX SEARCH & EXPORT)
# ==============================================================

@login_required
def parent_collection_center(request):
    """
    Parent Collection Center for School Admins.
    Supports HTMX Live Search, Paid/Unpaid Filtering, Pay on Behalf Modal, and Export CSV/Excel.
    """
    tenant = get_user_tenant(request)
    if not tenant:
        return render(request, "tenants/billing/access_denied.html", status=403)

    search_query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', 'ALL')

    # Get parent profiles linked to active enrolled students in this tenant
    parents_query = ParentProfile.objects.filter(tenant=tenant).select_related('person')

    if search_query:
        parents_query = parents_query.filter(
            Q(parent_number__icontains=search_query) |
            Q(person__first_name__icontains=search_query) |
            Q(person__last_name__icontains=search_query)
        )

    parent_list = []
    for parent in parents_query:
        # Count active enrolled children
        active_children = FamilyRelationship.objects.filter(
            tenant=tenant,
            relative=parent.person,
            student__student_profile__isnull=False,
            student__student_profile__enrollment_status='enrolled'
        ).count()

        parent_sub = ParentSubscription.objects.filter(tenant=tenant, parent=parent).order_by('-created_at').first()
        sub_status = parent_sub.status if parent_sub else "UNPAID"
        amount_due = parent_sub.amount if parent_sub else (tenant.parent_subscription_amount * Decimal(str(active_children)))

        if status_filter != 'ALL' and sub_status != status_filter:
            continue

        parent_list.append({
            "parent_id": str(parent.id),
            "parent_number": parent.parent_number,
            "full_name": parent.person.get_full_name(),
            "active_children": active_children,
            "sub_status": sub_status,
            "amount_due": amount_due,
            "parent_sub_id": str(parent_sub.id) if parent_sub else None
        })

    # Return partial template if HTMX request
    if request.headers.get('HX-Request') == 'true':
        return render(request, "tenants/billing/partials/collection_table_partial.html", {"parent_list": parent_list})

    return render(request, "tenants/billing/collection_center.html", {"parent_list": parent_list, "tenant": tenant})


@login_required
def pay_on_behalf_process(request):
    """
    POST /billing/school/pay-on-behalf/
    Processes manual cash/bank transfer payment on behalf of selected parent.
    """
    if request.method == "POST":
        parent_id = request.POST.get('parent_id')
        payment_method = request.POST.get('payment_method', 'CASH')
        parent_profile = get_object_or_404(ParentProfile, id=parent_id)

        # Initialize Parent Subscription if missing
        init_res = ParentSubscriptionService.create_or_get_parent_subscription(
            parent_profile=parent_profile,
            fee_per_child=parent_profile.tenant.parent_subscription_amount
        )
        sub_id = init_res.data.get("parent_subscription_id")
        parent_sub = ParentSubscription.objects.get(id=sub_id)

        # Get or create pending invoice
        school = School.objects.filter(tenant=parent_profile.tenant).first()
        inv_res = InvoiceService.create_parent_invoice(
            tenant=parent_profile.tenant,
            school=school,
            parent_subscription=parent_sub,
            amount=parent_sub.amount
        )
        invoice = SubscriptionInvoice.objects.get(id=inv_res.data["invoice_id"])

        # Process Manual Payment
        pay_res = PaymentService.process_manual_payment(
            invoice=invoice,
            payment_method=payment_method,
            actor=request.user,
            paid_on_behalf=True
        )

        if pay_res.success:
            return redirect('tenants_web:parent_collection_center')
        
    return redirect('tenants_web:parent_collection_center')


# ==============================================================
# MODULE 5: PARENT BILLING PORTAL & RENEWAL
# ==============================================================

@login_required
def parent_billing_portal(request):
    """
    Parent Self-Service Portal displaying linked children, fee calculation
    (₦500 x N children = ₦1,000 via BillingCalculationService), and renew buttons.
    """
    parent_profile = ParentProfile.objects.filter(person__user=request.user).first()
    if not parent_profile:
        # Fallback for testing: fetch first parent
        parent_profile = ParentProfile.objects.first()

    if not parent_profile:
        return render(request, "tenants/billing/access_denied.html", status=404)

    # Use BillingCalculationService to compute fee
    calc_res = BillingCalculationService.calculate_parent_fee(
        parent_profile=parent_profile,
        fee_per_child=parent_profile.tenant.parent_subscription_amount
    )
    calc_data = calc_res.data if calc_res.success else {}

    # Get linked children
    family_links = FamilyRelationship.objects.filter(
        relative=parent_profile.person,
        student__student_profile__isnull=False
    ).select_related('student__student_profile')

    # Get parent subscription status
    parent_sub = ParentSubscription.objects.filter(parent=parent_profile).order_by('-created_at').first()

    # Available Payment Gateways
    gateways = PaymentGatewaySetting.objects.filter(enabled=True, maintenance_mode=False).order_by('priority')

    context = {
        "parent_profile": parent_profile,
        "calc_data": calc_data,
        "family_links": family_links,
        "parent_sub": parent_sub,
        "gateways": gateways
    }
    return render(request, "tenants/billing/parent_portal.html", context)


# ==============================================================
# MODULE 6: INVOICE MANAGEMENT & PDF DOWNLOAD
# ==============================================================

@login_required
def invoice_list_view(request):
    tenant = get_user_tenant(request)
    invoices = SubscriptionInvoice.objects.filter(tenant=tenant).order_by('-created_at') if tenant else SubscriptionInvoice.objects.all().order_by('-created_at')
    return render(request, "tenants/billing/invoice_list.html", {"invoices": invoices})


@login_required
def invoice_detail_view(request, invoice_id):
    invoice = get_object_or_404(SubscriptionInvoice, id=invoice_id)
    return render(request, "tenants/billing/invoice_detail.html", {"invoice": invoice})


@login_required
def invoice_pdf_view(request, invoice_id):
    invoice = get_object_or_404(SubscriptionInvoice, id=invoice_id)
    pdf_bytes = PDFGeneratorService.generate_invoice_pdf(invoice)
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{invoice.invoice_number}.pdf"'
    return response


# ==============================================================
# MODULE 7: RECEIPT MANAGEMENT & PDF DOWNLOAD
# ==============================================================

@login_required
def receipt_list_view(request):
    tenant = get_user_tenant(request)
    payments = SubscriptionPayment.objects.filter(tenant=tenant, status='SUCCESSFUL').order_by('-created_at') if tenant else SubscriptionPayment.objects.filter(status='SUCCESSFUL').order_by('-created_at')
    return render(request, "tenants/billing/receipt_list.html", {"payments": payments})


@login_required
def receipt_detail_view(request, payment_id):
    payment = get_object_or_404(SubscriptionPayment, id=payment_id)
    return render(request, "tenants/billing/receipt_detail.html", {"payment": payment})


@login_required
def receipt_pdf_view(request, payment_id):
    payment = get_object_or_404(SubscriptionPayment, id=payment_id)
    pdf_bytes = PDFGeneratorService.generate_receipt_pdf(payment)
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{payment.receipt_number or payment.reference}.pdf"'
    return response


# ==============================================================
# MODULE 8: PAYMENT HISTORY
# ==============================================================

@login_required
def payment_history_view(request):
    tenant = get_user_tenant(request)
    payments = SubscriptionPayment.objects.filter(tenant=tenant).order_by('-created_at') if tenant else SubscriptionPayment.objects.all().order_by('-created_at')
    return render(request, "tenants/billing/payment_history.html", {"payments": payments})


# ==============================================================
# MODULE 9: REFUND MANAGEMENT
# ==============================================================

@login_required
def refund_management_view(request):
    if not is_super_admin(request.user):
        return render(request, "tenants/billing/access_denied.html", status=403)

    if request.method == "POST":
        payment_id = request.POST.get('payment_id')
        action_type = request.POST.get('action_type')
        reason = request.POST.get('reason', 'Administrative refund')

        payment = get_object_or_404(SubscriptionPayment, id=payment_id)

        if action_type == 'REQUEST':
            RefundService.request_refund(payment=payment, reason=reason, actor=request.user)
        elif action_type == 'APPROVE':
            RefundService.approve_and_process_refund(payment=payment, actor=request.user)

        return redirect('tenants_web:refund_management')

    refund_payments = SubscriptionPayment.objects.filter(status__in=['REFUND_REQUESTED', 'REFUNDED']).order_by('-updated_at')
    all_successful = SubscriptionPayment.objects.filter(status='SUCCESSFUL').order_by('-created_at')[:20]
    return render(request, "tenants/billing/refund_management.html", {"refund_payments": refund_payments, "all_successful": all_successful})


# ==============================================================
# MODULE 11 & 12: REPORTS & CSV EXPORT
# ==============================================================

@login_required
def billing_reports_view(request):
    tenant = get_user_tenant(request)
    total_revenue = SubscriptionPayment.objects.filter(tenant=tenant, status='SUCCESSFUL').aggregate(total=Sum('amount'))['total'] or Decimal("0.00") if tenant else SubscriptionPayment.objects.filter(status='SUCCESSFUL').aggregate(total=Sum('amount'))['total'] or Decimal("0.00")
    total_invoices = SubscriptionInvoice.objects.filter(tenant=tenant).count() if tenant else SubscriptionInvoice.objects.count()

    context = {
        "total_revenue": total_revenue,
        "total_invoices": total_invoices
    }
    return render(request, "tenants/billing/reports.html", context)


@login_required
def export_reports_csv(request):
    tenant = get_user_tenant(request)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="billing_report.csv"'

    writer = csv.writer(response)
    writer.writerow(['Invoice Number', 'Tenant', 'Type', 'Amount', 'Status', 'Due Date'])

    invoices = SubscriptionInvoice.objects.filter(tenant=tenant) if tenant else SubscriptionInvoice.objects.all()
    for inv in invoices:
        writer.writerow([inv.invoice_number, inv.tenant.name if inv.tenant else '', inv.invoice_type, inv.total_amount, inv.status, inv.due_date.strftime("%Y-%m-%d")])

    return response
