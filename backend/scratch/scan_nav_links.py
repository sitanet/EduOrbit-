import os
import re
import sys

backend_dir = r"c:\Users\user\Desktop\Development\SMS\backend"
sms_dir = r"c:\Users\user\Desktop\Development\SMS"
sys.path.insert(0, sms_dir)
sys.path.insert(0, backend_dir)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings.local')

import django
django.setup()

from django.urls import resolve, Resolver404
from django.test import Client

TEMPLATE_DIR = os.path.join(backend_dir, "templates")

href_pattern = re.compile(r'href=["\']([^"\']+)["\']')

findings = []

for root, dirs, files in os.walk(TEMPLATE_DIR):
    for file in files:
        if file.endswith(".html"):
            filepath = os.path.join(root, file)
            rel_path = os.path.relpath(filepath, backend_dir)
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            for line_idx, line in enumerate(lines, 1):
                matches = href_pattern.findall(line)
                for link in matches:
                    # Ignore external links, mailto, tel, anchor hashes on same page (#modal, etc), and jinja templates {{ ... }}
                    if link.startswith("http") or link.startswith("mailto") or link.startswith("tel") or link.startswith("{{") or link.startswith("{%"):
                        continue
                    
                    if link == "#":
                        findings.append({
                            "severity": "HIGH",
                            "file": rel_path,
                            "template": file,
                            "line": line_idx,
                            "evidence": line.strip(),
                            "link": link,
                            "root_cause": "Dead link pointing to dummy anchor hash '#'",
                            "recommended_fix": "Replace href='#' with actual registered Django URL endpoint."
                        })
                    elif link.startswith("javascript:"):
                        findings.append({
                            "severity": "MEDIUM",
                            "file": rel_path,
                            "template": file,
                            "line": line_idx,
                            "evidence": line.strip(),
                            "link": link,
                            "root_cause": "Link utilizes inline JavaScript string instead of proper Django URL routing or button trigger",
                            "recommended_fix": "Use proper HTML button element with event listener or Django URL route."
                        })
                    elif link.startswith("/"):
                        # Verify if URL resolves in Django URLconf
                        url_path = link.split("?")[0]
                        try:
                            match = resolve(url_path)
                        except Resolver404:
                            findings.append({
                                "severity": "CRITICAL",
                                "file": rel_path,
                                "template": file,
                                "line": line_idx,
                                "evidence": line.strip(),
                                "link": link,
                                "root_cause": f"URL path '{url_path}' is not registered in Django URLconf (404)",
                                "recommended_fix": f"Register route '{url_path}' in appropriate urls.py module or update template link to valid route."
                            })

import json
with open(os.path.join(backend_dir, "scratch", "nav_audit_results.json"), "w") as out:
    json.dump(findings, out, indent=2)

print(f"Navigation Audit Completed. Total navigation issues found: {len(findings)}")
