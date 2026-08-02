import os
import re

backend_dir = r"c:\Users\user\Desktop\Development\SMS\backend"

TEMPLATE_DIR = os.path.join(backend_dir, "templates")
APPS_DIR = os.path.join(backend_dir, "apps")

# Keywords
PLACEHOLDER_KEYWORDS = ["lorem ipsum", "todo", "fixme", "placeholder", "coming soon", "dummy", "sample", "mock", "test data"]
JS_ALERTS = [r"alert\(", r"console\.log\("]
DEAD_LINKS = [r'href="#"', r'onclick="return false"']
CODE_QUALITY = [r"pass\b", r"NotImplementedError", r"return \{\}", r"return \[\]"]
SWALLOWED_ERRORS = [r"except\s+Exception:\s*pass", r"except:\s*pass"]

issues = []

def scan_file(filepath, base_dir_name):
    rel_path = os.path.relpath(filepath, backend_dir)
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except Exception as e:
        return

    for i, line in enumerate(lines, 1):
        line_lower = line.lower()
        
        # 1. Placeholders
        for kw in PLACEHOLDER_KEYWORDS:
            if kw in line_lower:
                # Exclude comments explaining valid behavior if any, but catch UI or code placeholders
                # Filter out obvious false positives like file comments or standard django variables/methods
                issues.append({
                    "file": rel_path,
                    "line": i,
                    "type": "Placeholder/Mock",
                    "evidence": line.strip(),
                    "severity": "MEDIUM",
                    "description": f"Found placeholder keyword '{kw}'"
                })

        # 2. Dead navigation / alerts in template/js
        if filepath.endswith(".html"):
            for dl in DEAD_LINKS:
                if re.search(dl, line):
                    issues.append({
                        "file": rel_path,
                        "line": i,
                        "type": "Dead Link/Nav",
                        "evidence": line.strip(),
                        "severity": "HIGH",
                        "description": f"Found dead link pattern '{dl}'"
                    })
            for ja in JS_ALERTS:
                if re.search(ja, line):
                    issues.append({
                        "file": rel_path,
                        "line": i,
                        "type": "JS Debug/Alert",
                        "evidence": line.strip(),
                        "severity": "MEDIUM",
                        "description": f"Found JS pattern '{ja}'"
                    })

        # 3. Python code quality / placeholders
        if filepath.endswith(".py"):
            for cq in CODE_QUALITY:
                if re.search(cq, line):
                    issues.append({
                        "file": rel_path,
                        "line": i,
                        "type": "Code Quality Stub",
                        "evidence": line.strip(),
                        "severity": "LOW",
                        "description": f"Found code stub pattern '{cq}'"
                    })
            for se in SWALLOWED_ERRORS:
                if re.search(se, line):
                    issues.append({
                        "file": rel_path,
                        "line": i,
                        "type": "Swallowed Exception",
                        "evidence": line.strip(),
                        "severity": "HIGH",
                        "description": "Found swallowed exception pattern (except: pass)"
                    })

# Scan Templates
for root, dirs, files in os.walk(TEMPLATE_DIR):
    for file in files:
        if file.endswith(".html"):
            scan_file(os.path.join(root, file), "templates")

# Scan Apps
for root, dirs, files in os.walk(APPS_DIR):
    for file in files:
        if file.endswith(".py"):
            scan_file(os.path.join(root, file), "apps")

print(f"Total issues found: {len(issues)}")
import json
with open(os.path.join(backend_dir, "scratch", "audit_defects.json"), "w") as f:
    json.dump(issues, f, indent=2)
