"""
ReportLab PDF Generation Service for EduOrbit SaaS Platform.
Generates professional branded PDF documents for Invoices, Receipts, and Financial Reports.
"""

import io
import logging
from decimal import Decimal
from typing import Dict, Any, Optional

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from backend.apps.tenants.models import SubscriptionInvoice, SubscriptionPayment

logger = logging.getLogger(__name__)


class PDFGeneratorService:
    """
    Enterprise PDF Generator producing high quality ReportLab documents.
    """

    @classmethod
    def generate_invoice_pdf(cls, invoice: SubscriptionInvoice) -> bytes:
        """
        Generates a branded PDF document for a SubscriptionInvoice.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=22, textColor=colors.HexColor('#1E293B'), leading=26)
        subtitle_style = ParagraphStyle('DocSub', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#64748B'))
        heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=12, textColor=colors.HexColor('#0F172A'), leading=16)
        cell_style = ParagraphStyle('Cell', parent=styles['Normal'], fontSize=9, leading=12)
        cell_bold = ParagraphStyle('CellBold', parent=styles['Normal'], fontSize=9, fontName='Helvetica-Bold', leading=12)

        story = []

        # Header Banner
        tenant_name = invoice.tenant.name if invoice.tenant else "EduOrbit SaaS ERP"
        story.append(Paragraph(f"<b>{tenant_name}</b>", title_style))
        story.append(Paragraph("Platform Parent & Student Access Invoice", subtitle_style))
        story.append(Spacer(1, 12))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E1'), spaceAfter=15))

        # Invoice Metadata Table
        meta_data = [
            [Paragraph("<b>Invoice Number:</b>", cell_bold), Paragraph(invoice.invoice_number, cell_style),
             Paragraph("<b>Issue Date:</b>", cell_bold), Paragraph(invoice.created_at.strftime("%Y-%m-%d"), cell_style)],
            [Paragraph("<b>Invoice Type:</b>", cell_bold), Paragraph(invoice.get_invoice_type_display(), cell_style),
             Paragraph("<b>Due Date:</b>", cell_bold), Paragraph(invoice.due_date.strftime("%Y-%m-%d"), cell_style)],
            [Paragraph("<b>Status:</b>", cell_bold), Paragraph(f"<b>{invoice.status}</b>", cell_style),
             Paragraph("<b>School:</b>", cell_bold), Paragraph(invoice.school.name if invoice.school else "N/A", cell_style)]
        ]
        meta_table = Table(meta_data, colWidths=[1.5*inch, 2.2*inch, 1.3*inch, 2.2*inch])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 20))

        # Line Items Table
        story.append(Paragraph("<b>Billing Items & Summary</b>", heading_style))
        story.append(Spacer(1, 8))

        items_data = [
            [Paragraph("<b>Description</b>", cell_bold), Paragraph("<b>Qty / Children</b>", cell_bold), Paragraph("<b>Amount (NGN)</b>", cell_bold)]
        ]

        if invoice.invoice_type == 'PARENT' and invoice.parent_subscriptions.first():
            parent_sub = invoice.parent_subscriptions.first()
            desc = f"Parent Access Fee ({parent_sub.parent.person.get_full_name()})"
            qty = str(parent_sub.child_count)
        else:
            desc = "School Platform Activation Fee"
            qty = "1"

        items_data.append([
            Paragraph(desc, cell_style),
            Paragraph(qty, cell_style),
            Paragraph(f"₦{invoice.amount:,.2f}", cell_style)
        ])

        items_data.append([
            Paragraph("<b>Tax (0%)</b>", cell_bold),
            Paragraph("-", cell_style),
            Paragraph(f"₦{invoice.tax_amount:,.2f}", cell_style)
        ])

        items_data.append([
            Paragraph("<b>Total Amount Due</b>", cell_bold),
            Paragraph("-", cell_style),
            Paragraph(f"<b>₦{invoice.total_amount:,.2f}</b>", cell_bold)
        ])

        items_table = Table(items_data, colWidths=[4.2*inch, 1.3*inch, 1.7*inch])
        items_table.setStyle(TableStyle([
            ('HEADERBACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E2E8F0')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('ALIGN', (1, 0), (-1, -1), 'LEFT'),
        ]))
        story.append(items_table)
        story.append(Spacer(1, 30))

        # Footer Notice
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#E2E8F0'), spaceAfter=10))
        story.append(Paragraph("Thank you for using EduOrbit ERP. For support inquiries, contact support@eduorbit.com.", subtitle_style))

        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    @classmethod
    def generate_receipt_pdf(cls, payment: SubscriptionPayment) -> bytes:
        """
        Generates a branded PDF receipt document for a SubscriptionPayment.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=22, textColor=colors.HexColor('#166534'), leading=26)
        subtitle_style = ParagraphStyle('DocSub', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#64748B'))
        cell_style = ParagraphStyle('Cell', parent=styles['Normal'], fontSize=9, leading=12)
        cell_bold = ParagraphStyle('CellBold', parent=styles['Normal'], fontSize=9, fontName='Helvetica-Bold', leading=12)

        story = []

        tenant_name = payment.tenant.name if payment.tenant else "EduOrbit SaaS ERP"
        story.append(Paragraph(f"<b>{tenant_name}</b>", title_style))
        story.append(Paragraph("OFFICIAL PAYMENT RECEIPT", subtitle_style))
        story.append(Spacer(1, 12))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#22C55E'), spaceAfter=15))

        meta_data = [
            [Paragraph("<b>Receipt Number:</b>", cell_bold), Paragraph(payment.receipt_number or "REC-N/A", cell_style),
             Paragraph("<b>Payment Date:</b>", cell_bold), Paragraph(payment.paid_at.strftime("%Y-%m-%d %H:%M") if payment.paid_at else "N/A", cell_style)],
            [Paragraph("<b>Transaction Ref:</b>", cell_bold), Paragraph(payment.reference, cell_style),
             Paragraph("<b>Payment Gateway:</b>", cell_bold), Paragraph(payment.gateway, cell_style)],
            [Paragraph("<b>Payment Method:</b>", cell_bold), Paragraph(payment.payment_method, cell_style),
             Paragraph("<b>Payment Status:</b>", cell_bold), Paragraph(f"<b>{payment.status}</b>", cell_style)]
        ]
        meta_table = Table(meta_data, colWidths=[1.5*inch, 2.2*inch, 1.3*inch, 2.2*inch])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F0FDF4')),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 20))

        # Payment Amount Table
        amount_data = [
            [Paragraph("<b>Invoice Reference</b>", cell_bold), Paragraph("<b>Paid Amount (NGN)</b>", cell_bold)],
            [Paragraph(payment.invoice.invoice_number if payment.invoice else "N/A", cell_style), Paragraph(f"<b>₦{payment.amount:,.2f}</b>", cell_bold)]
        ]
        amount_table = Table(amount_data, colWidths=[4.5*inch, 2.7*inch])
        amount_table.setStyle(TableStyle([
            ('HEADERBACKGROUND', (0, 0), (-1, 0), colors.HexColor('#DCFCE7')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#86EFAC')),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(amount_table)
        story.append(Spacer(1, 30))

        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#E2E8F0'), spaceAfter=10))
        story.append(Paragraph("This is an official electronically generated payment receipt issued by EduOrbit ERP.", subtitle_style))

        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes
