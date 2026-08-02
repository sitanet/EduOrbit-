import json
import os

backend_dir = r"c:\Users\user\Desktop\Development\SMS\backend"

modules_missing_workflows = {
    "Academic": [
        {
            "page": "Gradebook & Matrix Score Entry",
            "file": "templates/academic/dashboard.html",
            "view": "AcademicDashboardWebView",
            "missing_workflow": "Multi-term class gradebook entry grid allowing teachers to enter assignment/exam scores for all students in one view.",
            "severity": "HIGH",
            "recommended_implementation": "Create GradebookWebView and gradebook.html matrix table with HTMX auto-save inputs."
        },
        {
            "page": "Automated Report Card Generation",
            "file": "templates/academic/dashboard.html",
            "view": "AcademicDashboardWebView",
            "missing_workflow": "End-of-term PDF report card compiler aggregating grades, attendance percentage, conduct notes, and principal signature.",
            "severity": "HIGH",
            "recommended_implementation": "Implement ReportCardService with ReportLab or WeasyPrint PDF compiler."
        },
        {
            "page": "Batch Student Promotion Engine",
            "file": "templates/academic/dashboard.html",
            "view": "AcademicDashboardWebView",
            "missing_workflow": "Automated end-of-year batch promotion workflow moving students to the next grade based on academic pass criteria.",
            "severity": "MEDIUM",
            "recommended_implementation": "Create PromotionWizardView allowing admins to set pass mark threshold and auto-promote class cohorts."
        }
    ],
    "Admissions": [
        {
            "page": "Automated Student ID Card Generation",
            "file": "templates/admissions/dashboard.html",
            "view": "AdmissionsDashboardWebView",
            "missing_workflow": "Barcode-equipped Student ID card PDF template generation upon applicant enrollment confirmation.",
            "severity": "MEDIUM",
            "recommended_implementation": "Build IDCardGenerator service with QR/barcode rendering for enrolled applicants."
        },
        {
            "page": "Admissions Fee Ledger Bridge",
            "file": "templates/admissions/wizard.html",
            "view": "AdmissionsWizardWebView",
            "missing_workflow": "Automatic posting of application and acceptance fees directly into the double-entry accounting ledger.",
            "severity": "HIGH",
            "recommended_implementation": "Connect application acceptance signal to GeneralLedger posting service in efbm."
        }
    ],
    "Students": [
        {
            "page": "Medical & Clinic Record Integration",
            "file": "templates/students/portfolio.html",
            "view": "StudentPortfolioWebView",
            "missing_workflow": "Direct visibility of student clinic consultation visits and allergy alerts on the main Student Portfolio page.",
            "severity": "MEDIUM",
            "recommended_implementation": "Pass clinic visit queryset into StudentPortfolioWebView context."
        }
    ],
    "Teachers": [
        {
            "page": "Teacher Appraisal & Performance View",
            "file": "templates/teachers/dashboard.html",
            "view": "TeacherDashboardWebView",
            "missing_workflow": "Teacher self-service view for viewing annual HR performance appraisal scores and supervisor feedback.",
            "severity": "MEDIUM",
            "recommended_implementation": "Add HR Appraisal summary widget to teacher dashboard workspace."
        }
    ],
    "Finance": [
        {
            "page": "Trial Balance Statement Generator",
            "file": "templates/efbm/dashboard.html",
            "view": "FinanceDashboardView",
            "missing_workflow": "Dynamic Trial Balance financial statement generator verifying debit and credit equality.",
            "severity": "HIGH",
            "recommended_implementation": "Create TrialBalanceView aggregating GeneralLedger balances."
        },
        {
            "page": "Income Statement & Balance Sheet Reports",
            "file": "templates/efbm/dashboard.html",
            "view": "FinanceDashboardView",
            "missing_workflow": "Automated Income Statement (P&L) and Balance Sheet financial reporting export views.",
            "severity": "HIGH",
            "recommended_implementation": "Build FinancialReportingService with PDF/Excel export."
        }
    ],
    "HR": [
        {
            "page": "Probation & Employee Confirmation Engine",
            "file": "templates/hr/admin/directory.html",
            "view": "EmployeeDirectoryView",
            "missing_workflow": "Formal probation review workflow and confirmation letter generation upon probation completion.",
            "severity": "MEDIUM",
            "recommended_implementation": "Add probation status tracker and PDF confirmation letter generator."
        },
        {
            "page": "Offboarding & Exit Clearance Checklist",
            "file": "templates/hr/admin/directory.html",
            "view": "EmployeeDirectoryView",
            "missing_workflow": "Exit interview logging, asset handover verification, and final settlement calculation.",
            "severity": "MEDIUM",
            "recommended_implementation": "Create ExitClearanceView tracking departmental sign-offs."
        }
    ],
    "Inventory": [
        {
            "page": "Goods Receipt Note (GRN) Verification",
            "file": "templates/inventory/items.html",
            "view": "InventoryItemWebView",
            "missing_workflow": "Purchase Order receiving workflow comparing ordered vs actual received stock quantities.",
            "severity": "HIGH",
            "recommended_implementation": "Build GoodsReceiptView updating inventory stock upon PO delivery."
        },
        {
            "page": "Inter-Warehouse Stock Transfer",
            "file": "templates/inventory/items.html",
            "view": "InventoryItemWebView",
            "missing_workflow": "Stock transfer request and approval UI between distinct campus warehouses.",
            "severity": "MEDIUM",
            "recommended_implementation": "Create StockTransferView executing dual StockMovement records."
        }
    ],
    "Library": [
        {
            "page": "Bulk Book Catalog Import",
            "file": "templates/library/catalog.html",
            "view": "LibraryCatalogView",
            "missing_workflow": "Excel/CSV bulk file upload for cataloging hundreds of library books simultaneously.",
            "severity": "MEDIUM",
            "recommended_implementation": "Implement BookImportView parsing Excel files with openpyxl."
        },
        {
            "page": "Overdue Fine Fee Posting",
            "file": "templates/library/dashboard.html",
            "view": "LibraryDashboardView",
            "missing_workflow": "Automated posting of library overdue fines to student ledger accounts in efbm.",
            "severity": "HIGH",
            "recommended_implementation": "Connect overdue book return view to student invoice creation."
        }
    ],
    "Hostel": [
        {
            "page": "Bed Transfer Workflow",
            "file": "templates/hostel/rooms.html",
            "view": "HostelRoomsView",
            "missing_workflow": "Room and bed transfer request approval tracking for resident boarders.",
            "severity": "MEDIUM",
            "recommended_implementation": "Add BedTransferView updating HostelBed allocations with audit log."
        }
    ],
    "Transport": [
        {
            "page": "Driver Licence & Route Fuel Analytics",
            "file": "templates/transport/routes.html",
            "view": "TransportRoutesView",
            "missing_workflow": "Driver licence expiration alerts and vehicle fuel efficiency tracking logs.",
            "severity": "MEDIUM",
            "recommended_implementation": "Add driver profiles and vehicle maintenance/fuel log forms."
        }
    ],
    "Clinic": [
        {
            "page": "Pharmacy Stock Auto-Deduction",
            "file": "templates/clinic/consultation.html",
            "view": "ClinicConsultationView",
            "missing_workflow": "Automatic deduction of prescribed medication quantities from clinic inventory stock upon dispensing.",
            "severity": "HIGH",
            "recommended_implementation": "Connect Prescription dispensing trigger to InventoryItem stock reduction."
        }
    ],
    "Exams": [
        {
            "page": "Exam Broadsheet View & PDF Export",
            "file": "templates/emrp/dashboard.html",
            "view": "EMRPDashboardView",
            "missing_workflow": "Class-wide exam broadsheet compilation showing raw marks, weighted averages, and positions.",
            "severity": "HIGH",
            "recommended_implementation": "Create BroadsheetView with PDF and Excel export routines."
        }
    ],
    "LMS": [
        {
            "page": "Assignment Submission Grading UI",
            "file": "templates/lms/dashboard.html",
            "view": "LMSDashboardView",
            "missing_workflow": "Teacher evaluation interface for reviewing student file submissions and giving inline feedback.",
            "severity": "MEDIUM",
            "recommended_implementation": "Add SubmissionGradingView with file previewer and mark input."
        }
    ],
    "Communication": [
        {
            "page": "SMS & Email Campaign Delivery Logs",
            "file": "templates/communication/dashboard.html",
            "view": "CommunicationDashboardView",
            "missing_workflow": "Detailed delivery log report showing sent, delivered, failed, and queued broadcast message statuses.",
            "severity": "MEDIUM",
            "recommended_implementation": "Create MessageDeliveryLogView displaying provider callback status."
        }
    ],
    "Workflow": [
        {
            "page": "Visual Approval Chain Builder",
            "file": "templates/workflow/dashboard.html",
            "view": "WorkflowDashboardView",
            "missing_workflow": "UI builder for configuring multi-step sequential or parallel approval levels per department.",
            "severity": "MEDIUM",
            "recommended_implementation": "Add interactive chain step editor to WorkflowDashboardView."
        }
    ],
    "Administration": [
        {
            "page": "System Audit Trail & Session Inspector",
            "file": "templates/administration/dashboard.html",
            "view": "AdminDashboardView",
            "missing_workflow": "Comprehensive log viewer inspecting active user sessions, IP addresses, and security events.",
            "severity": "MEDIUM",
            "recommended_implementation": "Add SessionInspectorView displaying active user sessions."
        }
    ],
    "Facilities": [
        {
            "page": "Facility Maintenance Ticketing",
            "file": "templates/facilities/dashboard.html",
            "view": "FacilitiesDashboardView",
            "missing_workflow": "Work order creation and vendor assignment for building repairs and equipment maintenance.",
            "severity": "LOW",
            "recommended_implementation": "Add MaintenanceWorkOrder model and ticketing UI."
        }
    ],
    "Analytics": [
        {
            "page": "Custom Report Builder & Export",
            "file": "templates/analytics/dashboard.html",
            "view": "AnalyticsDashboardView",
            "missing_workflow": "Ad-hoc query report builder allowing admins to select fields, filters, and export custom datasets.",
            "severity": "MEDIUM",
            "recommended_implementation": "Build ReportBuilderView supporting CSV/Excel generation."
        }
    ],
    "People": [
        {
            "page": "Bulk People Import & CSV Validation",
            "file": "templates/people/directory.html",
            "view": "PersonDirectoryWebView",
            "missing_workflow": "CSV upload parser for creating person profiles (staff, students, guardians) in bulk.",
            "severity": "MEDIUM",
            "recommended_implementation": "Add BulkPersonImportView with dry-run CSV validation."
        }
    ],
    "Tenants": [
        {
            "page": "Live Subscription MRR Billing Aggregator",
            "file": "templates/tenants/dashboard.html",
            "view": "TenantDashboardView",
            "missing_workflow": "Live MRR/ARR financial billing aggregation querying active subscription plans across multi-tenant schools.",
            "severity": "MEDIUM",
            "recommended_implementation": "Replace simulated MRR arithmetic with query aggregation on Subscription models."
        }
    ],
    "Dashboard": [
        {
            "page": "Quick Action Shortcut Customizer",
            "file": "templates/dashboards/school_admin_dashboard.html",
            "view": "SchoolAdminDashboardView",
            "missing_workflow": "User preference settings allowing administrators to customize their favorite dashboard quick action buttons.",
            "severity": "LOW",
            "recommended_implementation": "Add UserPreference setting for dashboard shortcuts grid."
        }
    ]
}

# Write summary to file
with open(os.path.join(backend_dir, "scratch", "functional_audit_summary.json"), "w") as out:
    json.dump(modules_missing_workflows, out, indent=2)

print(f"Compiled functional audit evidence across all {len(modules_missing_workflows)} applications.")
