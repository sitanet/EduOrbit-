import json
import os

scratch_dir = r"c:\Users\user\Desktop\Development\SMS\backend\scratch"
with open(os.path.join(scratch_dir, "audit_defects.json"), "r") as f:
    issues = json.load(f)

# Let's filter out common false positives:
# - files in templates/docs/ or scratch/
# - typical comments containing standard keywords
# - test files (test_*.py)

filtered = []
for iss in issues:
    fpath = iss["file"]
    # Filter out scratch, docs, tests, third party
    if "scratch\\" in fpath or "docs\\" in fpath or "tests\\" in fpath or "migrations\\" in fpath:
        continue
    # Filter out typical HTML input placeholder="..." attributes because they are standard placeholder attributes, not stubs
    if iss["type"] == "Placeholder/Mock" and 'placeholder="' in iss["evidence"]:
        continue
    # Filter out typical standard "pass" statements in empty __init__ files or models
    if iss["type"] == "Code Quality Stub" and iss["evidence"].strip() == "pass" and ("__init__.py" in fpath or "models.py" in fpath):
        continue
        
    filtered.append(iss)

print(f"Filtered down to {len(filtered)} real issues.")
with open(os.path.join(scratch_dir, "filtered_defects.json"), "w") as f:
    json.dump(filtered, f, indent=2)

for type_name in set(i["type"] for i in filtered):
    count = sum(1 for i in filtered if i["type"] == type_name)
    print(f"  {type_name}: {count}")
