import os
import re
import json

backend_dir = r"c:\Users\user\Desktop\Development\SMS\backend"
apps_dir = os.path.join(backend_dir, "apps")
templates_dir = os.path.join(backend_dir, "templates")

features_to_check = {
    "Gradebook": ["Gradebook", "gradebook", "GradeEntry"],
    "Report Cards": ["ReportCard", "report_card", "ReportCardService"],
    "Student Promotion": ["StudentPromotion", "promote_student", "PromotionWizard"],
    "Student ID Card": ["StudentIdCard", "id_card", "IDCardGenerator"],
    "Admissions to Ledger Bridge": ["AdmissionApplication", "GeneralLedger", "post_admission_fee"],
    "Trial Balance Report": ["TrialBalance", "trial_balance"],
    "Balance Sheet Report": ["BalanceSheet", "balance_sheet"],
    "Income Statement Report": ["IncomeStatement", "income_statement", "ProfitAndLoss"],
    "Probation & Confirmation": ["ProbationReview", "confirm_employee"],
    "Offboarding Exit Checklist": ["ExitClearance", "offboarding_checklist"],
    "Goods Receipt Note (GRN)": ["GoodsReceipt", "goods_receipt", "GRN"],
    "Inter-Warehouse Transfer": ["WarehouseTransfer", "transfer_stock"],
    "Library Overdue Fine Bridge": ["BookIssue", "fine_amount", "post_fine_to_ledger"],
    "Clinic to Inventory Bridge": ["Prescription", "deduct_stock", "InventoryItem"],
    "Exam Broadsheet": ["Broadsheet", "broadsheet_view"],
    "Payroll to GL Bridge": ["PayrollRun", "gl_entries", "post_payroll_to_gl"]
}

verification_results = {}

def search_codebase(keywords):
    found_in_models = []
    found_in_views = []
    found_in_services = []
    found_in_templates = []
    found_in_urls = []
    found_in_api = []
    
    # Search python files
    for root, dirs, files in os.walk(apps_dir):
        for file in files:
            if file.endswith(".py"):
                fpath = os.path.join(root, file)
                rel_path = os.path.relpath(fpath, backend_dir)
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    for kw in keywords:
                        if re.search(r'\b' + re.escape(kw) + r'\b', content, re.IGNORECASE):
                            if "models.py" in file:
                                found_in_models.append((rel_path, kw))
                            elif "views" in file:
                                found_in_views.append((rel_path, kw))
                            elif "services" in file or "service" in file:
                                found_in_services.append((rel_path, kw))
                            elif "urls.py" in file:
                                found_in_urls.append((rel_path, kw))
                            elif "api" in rel_path or "serializers" in file:
                                found_in_api.append((rel_path, kw))
                except Exception:
                    pass

    # Search template files
    for root, dirs, files in os.walk(templates_dir):
        for file in files:
            if file.endswith(".html"):
                fpath = os.path.join(root, file)
                rel_path = os.path.relpath(fpath, backend_dir)
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    for kw in keywords:
                        if re.search(r'\b' + re.escape(kw) + r'\b', content, re.IGNORECASE):
                            found_in_templates.append((rel_path, kw))
                except Exception:
                    pass

    return {
        "models": list(set(found_in_models)),
        "views": list(set(found_in_views)),
        "services": list(set(found_in_services)),
        "templates": list(set(found_in_templates)),
        "urls": list(set(found_in_urls)),
        "api": list(set(found_in_api)),
    }

for feat, kw_list in features_to_check.items():
    verification_results[feat] = search_codebase(kw_list)

with open(os.path.join(backend_dir, "scratch", "verified_repo_evidence.json"), "w") as out:
    json.dump(verification_results, out, indent=2)

print("Evidence verification script finished.")
