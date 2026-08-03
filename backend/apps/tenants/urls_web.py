from django.urls import path
from backend.apps.tenants.views_web import (
    super_admin_billing_dashboard,
    gateway_management,
    school_billing_dashboard,
    parent_collection_center,
    pay_on_behalf_process,
    parent_billing_portal,
    invoice_list_view,
    invoice_detail_view,
    invoice_pdf_view,
    receipt_list_view,
    receipt_detail_view,
    receipt_pdf_view,
    payment_history_view,
    refund_management_view,
    billing_reports_view,
    export_reports_csv
)

app_name = 'tenants_web'

urlpatterns = [
    # Module 1 & 2: Software Owner Dashboard & Gateway Manager
    path('billing/admin/dashboard/', super_admin_billing_dashboard, name='super_admin_dashboard'),
    path('billing/admin/gateways/', gateway_management, name='gateway_management'),

    # Module 3, 9 & 10: School Dashboard, Compliance & Collection Center
    path('billing/school/dashboard/', school_billing_dashboard, name='school_dashboard'),
    path('billing/school/collection-center/', parent_collection_center, name='parent_collection_center'),
    path('billing/school/pay-on-behalf/', pay_on_behalf_process, name='pay_on_behalf_process'),

    # Module 4: Parent Billing Portal & Renewal
    path('billing/parent/portal/', parent_billing_portal, name='parent_portal'),

    # Module 5 & 6: Invoice & Receipt Management
    path('billing/invoices/', invoice_list_view, name='invoice_list'),
    path('billing/invoices/<uuid:invoice_id>/', invoice_detail_view, name='invoice_detail'),
    path('billing/invoices/<uuid:invoice_id>/pdf/', invoice_pdf_view, name='invoice_pdf'),
    path('billing/receipts/', receipt_list_view, name='receipt_list'),
    path('billing/receipts/<uuid:payment_id>/', receipt_detail_view, name='receipt_detail'),
    path('billing/receipts/<uuid:payment_id>/pdf/', receipt_pdf_view, name='receipt_pdf'),

    # Module 7 & 8: Payment History & Refunds
    path('billing/payment-history/', payment_history_view, name='payment_history'),
    path('billing/refunds/', refund_management_view, name='refund_management'),

    # Module 11 & 12: Reports & Exports
    path('billing/reports/', billing_reports_view, name='billing_reports'),
    path('billing/reports/export/csv/', export_reports_csv, name='export_reports_csv'),
]
