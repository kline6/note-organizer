"""Frontend file validation - checks all Vue/TS files for obvious issues."""
import os
import re

base = os.path.dirname(os.path.abspath(__file__))
frontend_src = os.path.join(base, "frontend", "src")
errors = []

print("=" * 50)
print("Testing frontend files...")
print("=" * 50)

# Check all .vue and .ts files exist
files_to_check = [
    "main.ts",
    "App.vue",
    "env.d.ts",
    "types/index.ts",
    "api/index.ts",
    "stores/project.ts",
    "views/WorkspaceView.vue",
    "components/ProjectPanel.vue",
    "components/FileDropZone.vue",
    "components/NoteEditor.vue",
    "components/RuleEditor.vue",
    "components/ExportPanel.vue",
    "components/SnapshotPanel.vue",
    "components/SettingsPanel.vue",
]

for f in files_to_check:
    path = os.path.join(frontend_src, f)
    if os.path.exists(path):
        print(f"  [OK] {f}")
    else:
        print(f"  [FAIL] {f} not found")
        errors.append(f"Missing file: {f}")

# Check api/index.ts exports
print("\n" + "=" * 50)
print("Checking API exports...")
print("=" * 50)

api_path = os.path.join(frontend_src, "api", "index.ts")
with open(api_path, "r", encoding="utf-8") as f:
    api_content = f.read()

expected_exports = ["projectApi", "classifyApi", "exportApi", "ruleApi", "settingsApi"]
for exp in expected_exports:
    if f"export const {exp}" in api_content:
        print(f"  [OK] {exp} exported")
    else:
        print(f"  [FAIL] {exp} not exported")
        errors.append(f"API export missing: {exp}")

# Check RuleEditor.vue passes project_id
print("\n" + "=" * 50)
print("Checking RuleEditor passes project_id...")
print("=" * 50)

rule_editor_path = os.path.join(frontend_src, "components", "RuleEditor.vue")
with open(rule_editor_path, "r", encoding="utf-8") as f:
    re_content = f.read()

create_class_calls = re.findall(r'createClassification\(\{[^}]+\}\)', re_content, re.DOTALL)
for i, call in enumerate(create_class_calls):
    if 'project_id' in call:
        print(f"  [OK] createClassification call #{i+1} has project_id")
    else:
        print(f"  [FAIL] createClassification call #{i+1} missing project_id")
        errors.append(f"RuleEditor createClassification #{i+1} missing project_id")

create_hl_calls = re.findall(r'createHighlight\(\{[^}]+\}\)', re_content, re.DOTALL)
for i, call in enumerate(create_hl_calls):
    if 'project_id' in call:
        print(f"  [OK] createHighlight call #{i+1} has project_id")
    else:
        print(f"  [FAIL] createHighlight call #{i+1} missing project_id")
        errors.append(f"RuleEditor createHighlight #{i+1} missing project_id")

# Check App.vue imports SettingsPanel
print("\n" + "=" * 50)
print("Checking component wiring...")
print("=" * 50)

app_path = os.path.join(frontend_src, "App.vue")
with open(app_path, "r", encoding="utf-8") as f:
    app_content = f.read()

if "SettingsPanel" in app_content and "import SettingsPanel" in app_content:
    print(f"  [OK] App.vue imports SettingsPanel")
else:
    print(f"  [FAIL] App.vue missing SettingsPanel")
    errors.append("App.vue missing SettingsPanel import")

wv_path = os.path.join(frontend_src, "views", "WorkspaceView.vue")
with open(wv_path, "r", encoding="utf-8") as f:
    wv_content = f.read()

if "SettingsPanel" in wv_content and "import SettingsPanel" in wv_content:
    print(f"  [OK] WorkspaceView imports SettingsPanel")
else:
    print(f"  [FAIL] WorkspaceView missing SettingsPanel")
    errors.append("WorkspaceView missing SettingsPanel import")

# Check store.ts doesn't import computed
print("\n" + "=" * 50)
print("Checking unused imports...")
print("=" * 50)

store_path = os.path.join(frontend_src, "stores", "project.ts")
with open(store_path, "r", encoding="utf-8") as f:
    store_content = f.read()

if "computed" in store_content.split("import")[1].split("from")[0]:
    print(f"  [FAIL] store.ts still imports computed")
    errors.append("store.ts still imports computed")
else:
    print(f"  [OK] store.ts no unused computed import")

# Check NoteEditor.vue doesn't have redundant dynamic import
ne_path = os.path.join(frontend_src, "components", "NoteEditor.vue")
with open(ne_path, "r", encoding="utf-8") as f:
    ne_content = f.read()

if 'await import("@/api")' in ne_content:
    print(f"  [FAIL] NoteEditor.vue still has dynamic import")
    errors.append("NoteEditor.vue redundant dynamic import")
else:
    print(f"  [OK] NoteEditor.vue no redundant dynamic import")

# Summary
print("\n" + "=" * 50)
if errors:
    print(f"FAILED: {len(errors)} error(s)")
    for err in errors:
        print(f"  - {err}")
else:
    print("ALL FRONTEND CHECKS PASSED")
