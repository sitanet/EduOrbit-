import os
import re
import json

backend_dir = r"c:\Users\user\Desktop\Development\SMS\backend"

files_to_inspect = [
    "apps/academic/models.py",
    "apps/academic/services.py",
    "apps/academic/views_web.py",
    "apps/academic/urls.py",
    "apps/academic/migrations/0004_batchpromotionlog_gradebookentry_studentreportcard.py",
    "apps/academic/tests/test_academic_completion.py",
    "templates/academic/gradebook.html",
    "templates/academic/report_card.html",
    "templates/academic/promotions.html"
]

inspection_data = {}

for rel_path in files_to_inspect:
    abs_path = os.path.join(backend_dir, rel_path)
    if os.path.exists(abs_path):
        with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        inspection_data[rel_path] = {
            "exists": True,
            "line_count": len(content.splitlines()),
            "byte_count": len(content)
        }
    else:
        inspection_data[rel_path] = {"exists": False}

print(json.dumps(inspection_data, indent=2))
