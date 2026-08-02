import json
import os

backend_dir = r"c:\Users\user\Desktop\Development\SMS\backend"
with open(os.path.join(backend_dir, "scratch", "nav_audit_results.json"), "r") as f:
    findings = json.load(f)

# Group by severity
critical = [f for f in findings if f["severity"] == "CRITICAL"]
high = [f for f in findings if f["severity"] == "HIGH"]
medium = [f for f in findings if f["severity"] == "MEDIUM"]

print(f"CRITICAL: {len(critical)}")
print(f"HIGH: {len(high)}")
print(f"MEDIUM: {len(medium)}")

# Write formatted summary file for walkthrough
with open(os.path.join(backend_dir, "scratch", "formatted_nav_audit.txt"), "w", encoding="utf-8") as out:
    out.write("=== NAVIGATION AUDIT FINDINGS ===\n\n")
    for idx, item in enumerate(findings, 1):
        out.write(f"Issue #{idx}\n")
        out.write(f"Severity: {item['severity']}\n")
        out.write(f"File: {item['file']}\n")
        out.write(f"Template: {item['template']}\n")
        out.write(f"Line: {item['line']}\n")
        out.write(f"Evidence: {item['evidence']}\n")
        out.write(f"Root Cause: {item['root_cause']}\n")
        out.write(f"Recommended Fix: {item['recommended_fix']}\n")
        out.write("-" * 60 + "\n")
