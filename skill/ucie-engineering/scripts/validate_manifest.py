#!/usr/bin/env python3
"""Standard-library validator for the example UCIe project manifest."""
import argparse
import json
from pathlib import Path


def validate(data):
    errors, warnings = [], []
    if not isinstance(data, dict):
        return ["Top-level JSON value must be an object."], warnings
    for key in ("schema_version", "project", "baseline", "scope", "interfaces", "verification"):
        if key not in data:
            errors.append(f"Missing required top-level field: {key}")
    for parent, fields in {
        "project": ("name", "objective"),
        "baseline": ("standard", "revision", "specification_source"),
        "scope": ("in_scope", "out_of_scope"),
    }.items():
        obj = data.get(parent)
        if not isinstance(obj, dict):
            errors.append(f"{parent} must be an object.")
            continue
        for field in fields:
            if not obj.get(field):
                errors.append(f"Missing required field: {parent}.{field}")
    if isinstance(data.get("scope"), dict):
        for field in ("in_scope", "out_of_scope"):
            if not isinstance(data["scope"].get(field), list):
                errors.append(f"scope.{field} must be an array.")
    if not isinstance(data.get("interfaces"), list):
        errors.append("interfaces must be an array.")
    if not isinstance(data.get("verification"), dict):
        errors.append("verification must be an object.")
    baseline = data.get("baseline")
    if isinstance(baseline, dict) and baseline.get("source_status") == "requires_project_confirmation":
        warnings.append("Controlled specification source requires project confirmation.")
    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    try:
        data = json.loads(args.manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, indent=2))
        return 2
    errors, warnings = validate(data)
    print(json.dumps({"status": "invalid" if errors else "valid", "errors": errors, "warnings": warnings}, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
