"""Pure UCIe engineering helpers. No filesystem, network, shell, or EDA access."""
from __future__ import annotations

import json
import re
from typing import Any

MAX_JSON_CHARS = 200_000
IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_$]*$")


def _load_json(raw: str, label: str) -> Any:
    if not isinstance(raw, str):
        raise ValueError(f"{label} must be a JSON string.")
    if len(raw) > MAX_JSON_CHARS:
        raise ValueError(f"{label} exceeds the {MAX_JSON_CHARS}-character limit.")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} is invalid JSON: {exc.msg} at line {exc.lineno}.") from exc


def _identifier(value: str, label: str) -> str:
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
        raise ValueError(f"{label} must be a valid SystemVerilog identifier.")
    return value


def _single_line(value: str, label: str, limit: int = 1000) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string.")
    value = value.strip()
    if len(value) > limit or "\n" in value or "\r" in value:
        raise ValueError(f"{label} must be a single line of at most {limit} characters.")
    return value


def validate_project_manifest(manifest_json: str) -> dict[str, Any]:
    data = _load_json(manifest_json, "manifest_json")
    if not isinstance(data, dict):
        return {"status": "invalid", "errors": ["Top-level manifest must be an object."], "warnings": []}
    errors: list[str] = []
    warnings: list[str] = []
    required = {
        "schema_version": str,
        "project": dict,
        "baseline": dict,
        "scope": dict,
        "interfaces": list,
        "verification": dict,
    }
    for key, expected in required.items():
        if key not in data:
            errors.append(f"Missing required top-level field: {key}")
        elif not isinstance(data[key], expected):
            errors.append(f"{key} must be a {expected.__name__}.")
    nested = {
        "project": ("name", "objective"),
        "baseline": ("standard", "revision", "specification_source"),
        "scope": ("in_scope", "out_of_scope"),
    }
    for parent, fields in nested.items():
        obj = data.get(parent)
        if isinstance(obj, dict):
            for field in fields:
                value = obj.get(field)
                if value is None or value == "" or value == []:
                    errors.append(f"Missing required field: {parent}.{field}")
            if parent == "scope":
                for field in ("in_scope", "out_of_scope"):
                    if field in obj and not isinstance(obj[field], list):
                        errors.append(f"scope.{field} must be an array.")
            else:
                for field in fields:
                    if field in obj and not isinstance(obj[field], str):
                        errors.append(f"{parent}.{field} must be a string.")
    if isinstance(data.get("interfaces"), list):
        for index, item in enumerate(data["interfaces"]):
            if not isinstance(item, dict) or not isinstance(item.get("name"), str) or not item["name"].strip():
                errors.append(f"interfaces[{index}] must be an object with a non-empty name.")
    baseline = data.get("baseline")
    if isinstance(baseline, dict):
        if baseline.get("source_status") in (None, "", "requires_project_confirmation"):
            warnings.append("The controlled specification source still requires project confirmation.")
        if baseline.get("standard") and str(baseline["standard"]).upper() != "UCIE":
            warnings.append("baseline.standard is not UCIe; confirm this is intentional.")
    if data.get("schema_version") not in (None, "1.0"):
        warnings.append("Unknown schema_version; confirm validator compatibility.")
    return {
        "status": "invalid" if errors else "valid",
        "errors": errors,
        "warnings": warnings,
        "project_name": data.get("project", {}).get("name") if isinstance(data.get("project"), dict) else None,
        "baseline": baseline if isinstance(baseline, dict) else None,
    }


ARCHITECTURE_CHECKS = {
    "baseline": ("standard", "revision", "specification_source"),
    "scope": ("adapter_boundary", "package_topology", "selected_modes"),
    "interfaces": ("fdi_contract", "rdi_contract"),
    "mainband_sideband": ("mainband_definition", "sideband_definition", "clocking_assumptions"),
    "reliability": ("crc_definition", "retry_policy", "replay_buffer_policy", "error_injection_plan"),
    "flow_control": ("credit_model", "backpressure_behavior"),
    "power_reset": ("reset_sequence", "power_state_behavior", "clock_domain_assumptions"),
    "verification": ("testbench_architecture", "assertion_plan", "functional_coverage_plan"),
    "implementation": ("asic_toolchain", "fpga_toolchain", "timing_constraints"),
}


def review_architecture_inputs(architecture_json: str) -> dict[str, Any]:
    data = _load_json(architecture_json, "architecture_json")
    if not isinstance(data, dict):
        raise ValueError("architecture_json must contain a JSON object.")
    categories: dict[str, Any] = {}
    total = provided = 0
    for category, fields in ARCHITECTURE_CHECKS.items():
        present, missing = [], []
        section = data.get(category, {})
        for field in fields:
            total += 1
            value = section.get(field) if isinstance(section, dict) else None
            if value is None or value == "" or value == []:
                missing.append(field)
            else:
                present.append(field)
                provided += 1
        categories[category] = {"provided": present, "missing": missing}
    return {
        "status": "review_inputs_incomplete" if provided < total else "all_review_fields_populated",
        "populated_fields": provided,
        "review_fields": total,
        "completeness_percent": round(100 * provided / total, 1) if total else 100.0,
        "categories": categories,
        "disclaimer": "Completeness checklist only; not a normative UCIe compliance assessment. Mark out-of-scope items explicitly in the project record.",
    }


def generate_sv_module_shell(module_name: str, ports_json: str) -> str:
    module_name = _identifier(module_name, "module_name")
    ports = _load_json(ports_json, "ports_json")
    if not isinstance(ports, list) or len(ports) > 256:
        raise ValueError("ports_json must be an array containing no more than 256 ports.")
    seen: set[str] = set()
    declarations = []
    for index, port in enumerate(ports):
        if not isinstance(port, dict):
            raise ValueError(f"ports_json[{index}] must be an object.")
        name = _identifier(port.get("name"), f"ports_json[{index}].name")
        if name in seen:
            raise ValueError(f"Duplicate port name: {name}")
        seen.add(name)
        direction = port.get("direction")
        if direction not in ("input", "output", "inout"):
            raise ValueError(f"Port {name}: direction must be input, output, or inout.")
        width = port.get("width", 1)
        if not isinstance(width, int) or isinstance(width, bool) or not 1 <= width <= 4096:
            raise ValueError(f"Port {name}: width must be an integer from 1 to 4096.")
        signed = port.get("signed", False)
        if not isinstance(signed, bool):
            raise ValueError(f"Port {name}: signed must be boolean.")
        net = "wire" if direction == "inout" else "logic"
        sign = " signed" if signed else ""
        packed = f" [{width - 1}:0]" if width > 1 else ""
        declarations.append(f"    {direction:<6} {net}{sign}{packed} {name}")
    body = ",\n".join(declarations) if declarations else "    // TODO: add ports from the approved interface contract"
    return (
        f"module {module_name} (\n{body}\n);\n\n"
        "    // Functional behavior intentionally omitted.\n"
        "    // Add reset, clock, and handshake logic only from the approved interface contract.\n\n"
        "endmodule\n"
    )


def generate_sva_skeleton(property_name: str, clock: str, antecedent: str, consequent: str, disable_iff: str = "") -> str:
    property_name = _identifier(property_name, "property_name")
    clock = _identifier(clock, "clock")
    antecedent = _single_line(antecedent, "antecedent")
    consequent = _single_line(consequent, "consequent")
    if not isinstance(disable_iff, str) or len(disable_iff) > 500 or "\n" in disable_iff or "\r" in disable_iff:
        raise ValueError("disable_iff must be a single-line string of at most 500 characters.")
    disable = f"\n        disable iff ({disable_iff.strip()})" if disable_iff.strip() else ""
    return (
        f"property {property_name};\n"
        f"    @(posedge {clock}){disable}\n"
        f"        ({antecedent}) |-> ({consequent});\n"
        f"endproperty\n\nassert property ({property_name});\n"
    )


def generate_uvm_testplan(features_json: str, scope_note: str = "") -> str:
    features = _load_json(features_json, "features_json")
    if not isinstance(features, list) or len(features) > 100:
        raise ValueError("features_json must be an array of no more than 100 feature records.")
    if not isinstance(scope_note, str) or len(scope_note) > 2000:
        raise ValueError("scope_note must be a string of at most 2000 characters.")
    lines = [
        "# UVM Verification Plan Draft", "",
        "> Draft generated from supplied records. Verify each scenario against the selected UCIe revision and approved design contract. Missing inputs remain TODOs.", ""
    ]
    if scope_note.strip():
        lines += ["## Scope note", "", scope_note.strip(), ""]
    if not features:
        lines.append("No feature records supplied. Add explicit requirements before planning tests.")
        return "\n".join(lines)
    for index, feature in enumerate(features, 1):
        if not isinstance(feature, dict):
            raise ValueError(f"features_json[{index - 1}] must be an object.")
        fid = str(feature.get("id") or f"FEAT-{index:03d}")
        name = str(feature.get("name") or "Unnamed feature")
        src = feature.get("source_refs") or []
        if not isinstance(src, list):
            raise ValueError(f"{fid}.source_refs must be an array.")
        lines += [
            f"## {fid} — {name}", "",
            f"- Source references: {', '.join(map(str, src)) if src else 'TODO — exact revision, clause, and page required'}",
            f"- Requirement: {feature.get('requirement') or 'TODO: paraphrase the verified requirement.'}", "",
            f"### {fid}_NOMINAL",
            f"- Stimulus: {feature.get('nominal_stimulus') or 'TODO: define legal nominal stimulus.'}",
            f"- Expected: {feature.get('expected_result') or 'TODO: define source-backed expected behavior.'}", "",
        ]
        for field, heading, fallback in (
            ("boundary_cases", "BOUNDARY", "Derive limits from the selected specification; do not invent them."),
            ("negative_cases", "NEGATIVE", "Derive malformed/error cases from explicit requirements and fault models."),
            ("coverage_points", "COVERAGE", "Add requirement-driven coverpoints and justified crosses."),
        ):
            values = feature.get(field) or []
            if not isinstance(values, list):
                raise ValueError(f"{fid}.{field} must be an array.")
            lines += [f"### {fid}_{heading}"]
            lines += [f"- {value}" for value in values] if values else [f"- TODO: {fallback}"]
            lines.append("")
    lines += [
        "## Sign-off checklist", "",
        "- [ ] Every feature maps to an exact source revision and clause.",
        "- [ ] Every test has stimulus, expected result, and pass/fail criteria.",
        "- [ ] Reset, clock, backpressure, boundary, and error cases are covered where applicable.",
        "- [ ] Coverage is requirement-driven; exclusions are justified.",
        "- [ ] Regression evidence records tool version, seed, logs, and source revision.",
        "- [ ] No missing evidence is marked PASS.",
    ]
    return "\n".join(lines)


def audit_traceability_matrix(rows_json: str) -> dict[str, Any]:
    rows = _load_json(rows_json, "rows_json")
    if not isinstance(rows, list) or len(rows) > 1000:
        raise ValueError("rows_json must be an array of no more than 1000 rows.")
    required = ("requirement_id", "source_ref", "design_ref", "test_id", "result", "evidence_ref")
    allowed = {"PASS", "FAIL", "BLOCKED", "NOT_RUN", "NOT_APPLICABLE"}
    findings = []
    gaps = 0
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"rows_json[{index}] must be an object.")
        missing = [key for key in required if row.get(key) in (None, "", [])]
        result = str(row.get("result", "")).upper()
        issues = []
        if result and result not in allowed:
            issues.append(f"Unknown result status: {result}")
        if result == "FAIL" and not row.get("issue_ref"):
            issues.append("FAIL row should link an issue_ref.")
        if missing or issues:
            gaps += 1
        findings.append({"row": index, "requirement_id": row.get("requirement_id"), "missing_fields": missing, "issues": issues})
    return {
        "status": "complete_fields" if not gaps else "gaps_found",
        "rows_audited": len(rows),
        "rows_with_gaps": gaps,
        "completeness_percent": round(100 * (len(rows) - gaps) / len(rows), 1) if rows else 100.0,
        "findings": findings,
        "disclaimer": "Field audit only. Evidence paths are not opened, results are not independently verified, and this is not a compliance assessment.",
    }


def crc16_ccitt_false(data_hex: str) -> dict[str, Any]:
    if not isinstance(data_hex, str) or not data_hex.strip():
        raise ValueError("data_hex must contain hexadecimal bytes.")
    cleaned = re.sub(r"[\s:_-]", "", data_hex.strip())
    if cleaned.lower().startswith("0x"):
        cleaned = cleaned[2:]
    if not cleaned or len(cleaned) % 2 or not re.fullmatch(r"[0-9a-fA-F]+", cleaned):
        raise ValueError("data_hex must contain an even number of hexadecimal digits.")
    data = bytes.fromhex(cleaned)
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return {
        "algorithm": "CRC-16/CCITT-FALSE",
        "width": 16,
        "polynomial": "0x1021",
        "initial_value": "0xFFFF",
        "refin": False,
        "refout": False,
        "xorout": "0x0000",
        "input_bytes": len(data),
        "crc": f"0x{crc:04X}",
        "check_vector": {"ascii": "123456789", "expected_crc": "0x29B1"},
        "ucie_specific": False,
        "warning": "Generic CRC-16/CCITT-FALSE only. Not a UCIe CRC model unless the selected specification and independent validation establish equivalence.",
    }
