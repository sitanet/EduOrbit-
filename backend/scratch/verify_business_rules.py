import os
import re
import json

backend_dir = r"c:\Users\user\Desktop\Development\SMS\backend"
apps_dir = os.path.join(backend_dir, "apps")

rules_check = {
    "payroll_unique_run": ("apps/hr/models.py", ["unique_together", "PayrollRun", "period"]),
    "attendance_unique_date": ("apps/attendance/models.py", ["unique_together", "AttendanceRecord", "date"]),
    "hostel_bed_allocation": ("apps/hostel/models.py", ["HostelBed", "is_occupied", "allocated"]),
    "inventory_negative_stock": ("apps/inventory/models.py", ["current_quantity", "MinValueValidator"]),
    "invoice_delete_protection": ("apps/efbm/models.py", ["Invoice", "on_delete", "PROTECT"]),
    "discharged_student_book_issue": ("apps/library/models.py", ["BookIssue", "is_active", "status"]),
    "inactive_staff_clockin": ("apps/hr/models.py", ["clock_in", "is_active", "EmployeeProfile"])
}

rule_evidence = {}

for rule_name, (file_rel, kws) in rules_check.items():
    fpath = os.path.join(backend_dir, file_rel)
    found_lines = []
    if os.path.exists(fpath):
        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        for idx, line in enumerate(lines, 1):
            if any(kw.lower() in line.lower() for kw in kws):
                found_lines.append((idx, line.strip()))
    rule_evidence[rule_name] = {
        "file": file_rel,
        "matches": found_lines
    }

with open(os.path.join(backend_dir, "scratch", "business_rules_evidence.json"), "w") as out:
    json.dump(rule_evidence, out, indent=2)

print("Business rules verification finished.")
