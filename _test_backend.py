"""Backend syntax and import test script."""
import sys
import os
import traceback

# Change to backend directory
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
sys.path.insert(0, backend_dir)
os.chdir(backend_dir)

errors = []

# Test 1: Import config
print("=" * 50)
print("Testing backend imports...")
print("=" * 50)

tests = [
    ("app.config", "config"),
    ("app.database", "database"),
    ("app.models.project", "models.project"),
    ("app.models.note", "models.note"),
    ("app.models.rule", "models.rule"),
    ("app.models.snapshot", "models.snapshot"),
    ("app.schemas.project", "schemas.project"),
    ("app.schemas.note", "schemas.note"),
    ("app.schemas.rule", "schemas.rule"),
    ("app.settings_manager", "settings_manager"),
    ("app.services.file_service", "services.file_service"),
    ("app.services.export_service", "services.export_service"),
    ("app.services.ai_service", "services.ai_service"),
    ("app.services.classification_service", "services.classification_service"),
    ("app.routers.project", "routers.project"),
    ("app.routers.classify", "routers.classify"),
    ("app.routers.export", "routers.export"),
    ("app.routers.rule", "routers.rule"),
    ("app.routers.settings", "routers.settings"),
    ("app.main", "main"),
]

for module_name, label in tests:
    try:
        __import__(module_name)
        print(f"  [OK] {label}")
    except Exception as e:
        print(f"  [FAIL] {label}: {e}")
        errors.append((label, str(e), traceback.format_exc()))

# Test 2: Check models relationships
print("\n" + "=" * 50)
print("Testing model relationships...")
print("=" * 50)

try:
    from app.models.project import Project
    from app.models.note import NoteFile, NoteEntry
    from app.models.rule import ClassificationRule, HighlightRule
    from app.models.snapshot import Snapshot

    # Check Project relationships
    rels = [r.key for r in Project.__mapper__.relationships]
    expected = ['note_files', 'rules', 'highlight_rules', 'snapshots']
    for e in expected:
        if e in rels:
            print(f"  [OK] Project.{e}")
        else:
            print(f"  [FAIL] Project.{e} missing! Got: {rels}")
            errors.append(("Project relationships", f"Missing {e}"))

    # Check ClassificationRule FK
    cr_cols = [c.key for c in ClassificationRule.__table__.columns]
    if 'project_id' in cr_cols:
        print(f"  [OK] ClassificationRule.project_id")
    else:
        print(f"  [FAIL] ClassificationRule.project_id missing")
        errors.append(("ClassificationRule FK", "project_id missing"))

    # Check HighlightRule FK + relationship
    hr_cols = [c.key for c in HighlightRule.__table__.columns]
    if 'project_id' in hr_cols:
        print(f"  [OK] HighlightRule.project_id")
    else:
        print(f"  [FAIL] HighlightRule.project_id missing")
        errors.append(("HighlightRule FK", "project_id missing"))

    hr_rels = [r.key for r in HighlightRule.__mapper__.relationships]
    if 'project' in hr_rels:
        print(f"  [OK] HighlightRule.project relationship")
    else:
        print(f"  [FAIL] HighlightRule.project relationship missing")
        errors.append(("HighlightRule relationship", "project missing"))

except Exception as e:
    print(f"  [FAIL] Model check failed: {e}")
    errors.append(("Model check", str(e), traceback.format_exc()))

# Test 3: Check schema fields
print("\n" + "=" * 50)
print("Testing schema fields...")
print("=" * 50)

try:
    from app.schemas.rule import ClassificationRuleCreate, HighlightRuleCreate
    cr_fields = ClassificationRuleCreate.model_fields
    for f in ['project_id', 'pattern', 'target_file', 'priority']:
        if f in cr_fields:
            print(f"  [OK] ClassificationRuleCreate.{f}")
        else:
            print(f"  [FAIL] ClassificationRuleCreate.{f} missing")
            errors.append(("Schema field", f"ClassificationRuleCreate.{f} missing"))

    hr_fields = HighlightRuleCreate.model_fields
    for f in ['project_id', 'pattern', 'color']:
        if f in hr_fields:
            print(f"  [OK] HighlightRuleCreate.{f}")
        else:
            print(f"  [FAIL] HighlightRuleCreate.{f} missing")
            errors.append(("Schema field", f"HighlightRuleCreate.{f} missing"))

except Exception as e:
    print(f"  [FAIL] Schema check failed: {e}")
    errors.append(("Schema check", str(e), traceback.format_exc()))

# Summary
print("\n" + "=" * 50)
if errors:
    print(f"FAILED: {len(errors)} error(s)")
    for err in errors:
        print(f"  - {err[0]}: {err[1]}")
        if len(err) > 2:
            print(err[2][:500])
    sys.exit(1)
else:
    print("ALL TESTS PASSED")
    sys.exit(0)
