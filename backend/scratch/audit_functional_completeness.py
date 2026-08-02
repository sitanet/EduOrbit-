import os
import re
import json

backend_dir = r"c:\Users\user\Desktop\Development\SMS\backend"
TEMPLATE_DIR = os.path.join(backend_dir, "templates")

modules = [
    "academic", "admissions", "students", "teachers", "finance", "hr",
    "inventory", "library", "hostel", "transport", "clinic", "exams",
    "lms", "communication", "workflow", "administration", "facilities",
    "analytics", "people", "tenants", "dashboards"
]

def analyze_template(filepath):
    rel_path = os.path.relpath(filepath, backend_dir)
    filename = os.path.basename(filepath)
    
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    lines = content.splitlines()

    has_forms = "<form" in content
    has_post_forms = 'method="post"' in content.lower() or 'method="POST"' in content
    has_export = any(x in content.lower() for x in ["export", "download pdf", "excel", "csv", "print"])
    has_import = "import" in content.lower() or "upload" in content.lower()
    has_modal = "modal" in content.lower() or 'x-show="' in content.lower() or 'id="' in content.lower()
    has_htmx = "hx-get" in content or "hx-post" in content or "hx-delete" in content or "hx-target" in content
    has_table = "<table" in content
    has_buttons = "<button" in content or 'class="btn' in content or "px-4 py-2" in content
    
    # Check for empty state / missing actions
    missing_actions = []
    
    if has_table and not (has_forms or has_modal or has_htmx or "delete" in content.lower() or "edit" in content.lower()):
        missing_actions.append("Table rendered without inline Edit/Delete/Action buttons")
        
    if not has_export:
        missing_actions.append("Missing Export (PDF/Excel/CSV) action button")
        
    if not has_import:
        missing_actions.append("Missing Batch Import / File Upload functionality")

    return {
        "file": rel_path,
        "filename": filename,
        "has_forms": has_forms,
        "has_post_forms": has_post_forms,
        "has_export": has_export,
        "has_import": has_import,
        "has_htmx": has_htmx,
        "has_table": has_table,
        "missing_actions": missing_actions
    }

module_audits = {}

for mod in modules:
    mod_dir = os.path.join(TEMPLATE_DIR, mod)
    if os.path.exists(mod_dir):
        templates_info = []
        for root, dirs, files in os.walk(mod_dir):
            for file in files:
                if file.endswith(".html"):
                    info = analyze_template(os.path.join(root, file))
                    templates_info.append(info)
        module_audits[mod] = templates_info

with open(os.path.join(backend_dir, "scratch", "functional_completeness_data.json"), "w") as out:
    json.dump(module_audits, out, indent=2)

print("Functional Completeness Scan Completed.")
