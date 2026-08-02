import json
import os

scratch_dir = r"c:\Users\user\Desktop\Development\SMS\backend\scratch"
with open(os.path.join(scratch_dir, "filtered_defects.json"), "r") as f:
    issues = json.load(f)

with open(os.path.join(scratch_dir, "severe_defects.txt"), "w", encoding="utf-8") as out:
    out.write("=== DEAD LINKS / NAV ===\n")
    for i in issues:
        if i["type"] == "Dead Link/Nav":
            out.write(f'{i["file"]}:{i["line"]} => {i["evidence"]}\n')

    out.write("\n=== JS DEBUG / ALERT ===\n")
    for i in issues:
        if i["type"] == "JS Debug/Alert":
            out.write(f'{i["file"]}:{i["line"]} => {i["evidence"]}\n')

    out.write("\n=== PLACEHOLDERS / MOCKS ===\n")
    for i in issues:
        if i["type"] == "Placeholder/Mock" and ("coming soon" in i["evidence"].lower() or "dummy" in i["evidence"].lower() or "mock" in i["evidence"].lower()):
            out.write(f'{i["file"]}:{i["line"]} => {i["evidence"]}\n')
print("Successfully wrote severe defects to severe_defects.txt")
