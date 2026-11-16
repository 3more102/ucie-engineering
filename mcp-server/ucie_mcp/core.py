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


def _disable_iff(value: str) -> str:
    if not isinstance(value, str) or len(value) > 500 or "\n" in value or "\r" in value:
        raise ValueError("disable_iff must be a single-line string of at most 500 characters.")
    return value.strip()


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


def generate_sva_skeleton(
    property_name: str,
    clock: str,
    antecedent: str,
    consequent: str,
    disable_iff: str = "",
    implication: str = "|->",
) -> str:
    property_name = _identifier(property_name, "property_name")
    clock = _identifier(clock, "clock")
    antecedent = _single_line(antecedent, "antecedent")
    consequent = _single_line(consequent, "consequent")
    disable_iff = _disable_iff(disable_iff)
    if implication not in ("|->", "|=>"):
        raise ValueError("implication must be either '|->' (overlapped) or '|=>' (non-overlapped).")
    disable = f"\n        disable iff ({disable_iff})" if disable_iff else ""
    return (
        f"property {property_name};\n"
        f"    @(posedge {clock}){disable}\n"
        f"        ({antecedent}) {implication} ({consequent});\n"
        f"endproperty\n\nassert property ({property_name});\n"
    )


def generate_ready_valid_sva(
    prefix: str,
    clock: str,
    valid: str,
    ready: str,
    payload: str,
    disable_iff: str = "",
) -> str:
    """Generate generic ready/valid hold assertions; this is not a UCIe interface definition."""
    prefix = _identifier(prefix, "prefix")
    clock = _identifier(clock, "clock")
    valid = _identifier(valid, "valid")
    ready = _identifier(ready, "ready")
    payload = _identifier(payload, "payload")
    disable_iff = _disable_iff(disable_iff)
    disable = f"\n        disable iff ({disable_iff})" if disable_iff else ""
    stalled = f"({valid} && !{ready})"
    valid_property = f"p_{prefix}_valid_held_while_stalled"
    payload_property = f"p_{prefix}_payload_stable_while_stalled"
    return (
        "// Generic ready/valid contract template; confirm it matches the approved interface.\n"
        f"property {valid_property};\n"
        f"    @(posedge {clock}){disable}\n"
        f"        {stalled} |=> {valid};\n"
        "endproperty\n"
        f"assert property ({valid_property});\n\n"
        f"property {payload_property};\n"
        f"    @(posedge {clock}){disable}\n"
        f"        {stalled} |=> $stable({payload});\n"
        "endproperty\n"
        f"assert property ({payload_property});\n"
    )


def generate_uvm_agent_skeleton(agent_name: str, interface_type: str, fields_json: str) -> str:
    """Generate UVM class shells; driver and monitor behavior remain TODOs."""
    agent_name = _identifier(agent_name, "agent_name")
    interface_type = _identifier(interface_type, "interface_type")
    fields = _load_json(fields_json, "fields_json")
    if not isinstance(fields, list) or not 1 <= len(fields) <= 128:
        raise ValueError("fields_json must be an array containing 1 to 128 transaction fields.")
    seen: set[str] = set()
    declarations: list[str] = []
    field_macros: list[str] = []
    for index, field in enumerate(fields):
        if not isinstance(field, dict):
            raise ValueError(f"fields_json[{index}] must be an object.")
        name = _identifier(field.get("name"), f"fields_json[{index}].name")
        if name in seen:
            raise ValueError(f"Duplicate transaction field: {name}")
        seen.add(name)
        width = field.get("width", 1)
        if not isinstance(width, int) or isinstance(width, bool) or not 1 <= width <= 4096:
            raise ValueError(f"Field {name}: width must be an integer from 1 to 4096.")
        signed = field.get("signed", False)
        if not isinstance(signed, bool):
            raise ValueError(f"Field {name}: signed must be boolean.")
        sign = " signed" if signed else ""
        packed = f" [{width - 1}:0]" if width > 1 else ""
        declarations.append(f"    rand bit{sign}{packed} {name};")
        field_macros.append(f"    `uvm_field_int({name}, UVM_DEFAULT)")
    item = f"{agent_name}_item"
    sequencer = f"{agent_name}_sequencer"
    driver = f"{agent_name}_driver"
    monitor = f"{agent_name}_monitor"
    agent = f"{agent_name}_agent"
    sequence = f"{agent_name}_smoke_seq"
    package = f"{agent_name}_agent_pkg"
    return (
        "// UVM scaffold only: implement and review every TODO against the actual interface contract.\n"
        f"package {package};\n"
        "  import uvm_pkg::*;\n"
        '  `include "uvm_macros.svh"\n\n'
        f"  class {item} extends uvm_sequence_item;\n"
        + "\n".join(declarations) + "\n"
        + f"    `uvm_object_utils_begin({item})\n"
        + "\n".join(field_macros) + "\n"
        + "    `uvm_object_utils_end\n"
        + f'    function new(string name = "{item}"); super.new(name); endfunction\n'
        + "  endclass\n\n"
        + f"  class {sequencer} extends uvm_sequencer #({item});\n"
        + f"    `uvm_component_utils({sequencer})\n"
        + f'    function new(string name = "{sequencer}", uvm_component parent = null); super.new(name, parent); endfunction\n'
        + "  endclass\n\n"
        + f"  class {sequence} extends uvm_sequence #({item});\n"
        + f"    `uvm_object_utils({sequence})\n"
        + f'    function new(string name = "{sequence}"); super.new(name); endfunction\n'
        + "    task body();\n"
        + f"      {item} req_item;\n"
        + f'      req_item = {item}::type_id::create("req_item");\n'
        + "      start_item(req_item);\n"
        + '      if (!req_item.randomize()) `uvm_error("RAND", "Transaction randomization failed")\n'
        + "      finish_item(req_item);\n"
        + "    endtask\n"
        + "  endclass\n\n"
        + f"  class {driver} extends uvm_driver #({item});\n"
        + f"    `uvm_component_utils({driver})\n"
        + f"    virtual {interface_type} vif;\n"
        + f'    function new(string name = "{driver}", uvm_component parent = null); super.new(name, parent); endfunction\n'
        + "    function void build_phase(uvm_phase phase);\n"
        + "      super.build_phase(phase);\n"
        + f'      if (!uvm_config_db #(virtual {interface_type})::get(this, "", "vif", vif))\n'
        + f'        `uvm_fatal("NOVIF", "Virtual interface not configured for {driver}")\n'
        + "    endfunction\n"
        + "    // TODO: implement run_phase, sequence-item consumption, and pin driving.\n"
        + "  endclass\n\n"
        + f"  class {monitor} extends uvm_monitor;\n"
        + f"    `uvm_component_utils({monitor})\n"
        + f"    virtual {interface_type} vif;\n"
        + f"    uvm_analysis_port #({item}) analysis_port;\n"
        + f'    function new(string name = "{monitor}", uvm_component parent = null);\n'
        + "      super.new(name, parent);\n"
        + '      analysis_port = new("analysis_port", this);\n'
        + "    endfunction\n"
        + "    function void build_phase(uvm_phase phase);\n"
        + "      super.build_phase(phase);\n"
        + f'      if (!uvm_config_db #(virtual {interface_type})::get(this, "", "vif", vif))\n'
        + f'        `uvm_fatal("NOVIF", "Virtual interface not configured for {monitor}")\n'
        + "    endfunction\n"
        + "    // TODO: implement run_phase sampling and analysis_port.write().\n"
        + "  endclass\n\n"
        + f"  class {agent} extends uvm_agent;\n"
        + f"    `uvm_component_utils({agent})\n"
        + f"    virtual {interface_type} vif;\n"
        + f"    {monitor} monitor;\n"
        + f"    {driver} driver;\n"
        + f"    {sequencer} sequencer;\n"
        + f'    function new(string name = "{agent}", uvm_component parent = null); super.new(name, parent); endfunction\n'
        + "    function void build_phase(uvm_phase phase);\n"
        + "      super.build_phase(phase);\n"
        + f'      if (!uvm_config_db #(virtual {interface_type})::get(this, "", "vif", vif))\n'
        + f'        `uvm_fatal("NOVIF", "Virtual interface not configured for {agent}")\n'
        + f'      uvm_config_db #(virtual {interface_type})::set(this, "monitor", "vif", vif);\n'
        + f'      monitor = {monitor}::type_id::create("monitor", this);\n'
        + "      if (is_active == UVM_ACTIVE) begin\n"
        + f'        uvm_config_db #(virtual {interface_type})::set(this, "driver", "vif", vif);\n'
        + f'        driver = {driver}::type_id::create("driver", this);\n'
        + f'        sequencer = {sequencer}::type_id::create("sequencer", this);\n'
        + "      end\n"
        + "    endfunction\n"
        + "    function void connect_phase(uvm_phase phase);\n"
        + "      super.connect_phase(phase);\n"
        + "      if (is_active == UVM_ACTIVE) driver.seq_item_port.connect(sequencer.seq_item_export);\n"
        + "    endfunction\n"
        + "  endclass\n\n"
        + f"endpackage : {package}\n"
    )



def _ready_valid_contract_data(contract_json: str) -> tuple[dict[str, Any], list[str], list[str]]:
    data = _load_json(contract_json, "contract_json")
    if not isinstance(data, dict):
        raise ValueError("contract_json must contain a JSON object.")
    errors: list[str] = []
    warnings: list[str] = []
    if data.get("schema_version") != "1.0":
        errors.append("schema_version must be '1.0'.")
    identifiers: dict[str, str] = {}
    for key in ("interface_name", "agent_name", "clock", "valid", "ready"):
        try:
            identifiers[key] = _identifier(data.get(key), key)
        except ValueError as exc:
            errors.append(str(exc))
    if data.get("role") not in ("source", "sink"):
        errors.append("role must be either 'source' or 'sink'.")
    drive_edge, sample_edge = data.get("drive_edge"), data.get("sample_edge")
    if drive_edge not in ("posedge", "negedge"):
        errors.append("drive_edge must be 'posedge' or 'negedge'.")
    if sample_edge not in ("posedge", "negedge"):
        errors.append("sample_edge must be 'posedge' or 'negedge'.")
    if drive_edge in ("posedge", "negedge") and sample_edge in ("posedge", "negedge") and drive_edge == sample_edge:
        errors.append("drive_edge and sample_edge must differ to avoid same-edge drive/sample races.")
    if data.get("reset") not in (None, "", {}):
        errors.append("Reset handling is not generated. Remove 'reset' and add project-specific reset behavior before integration.")
    payload = data.get("payload")
    normalized_payload: list[dict[str, Any]] = []
    if not isinstance(payload, list) or not 1 <= len(payload) <= 64:
        errors.append("payload must be an array containing 1 to 64 fields.")
    else:
        for i, field in enumerate(payload):
            if not isinstance(field, dict):
                errors.append(f"payload[{i}] must be an object.")
                continue
            try:
                name = _identifier(field.get("name"), f"payload[{i}].name")
            except ValueError as exc:
                errors.append(str(exc))
                continue
            width, signed = field.get("width", 1), field.get("signed", False)
            if not isinstance(width, int) or isinstance(width, bool) or not 1 <= width <= 4096:
                errors.append(f"payload[{i}].width must be an integer from 1 to 4096.")
                continue
            if not isinstance(signed, bool):
                errors.append(f"payload[{i}].signed must be boolean.")
                continue
            normalized_payload.append({"name": name, "width": width, "signed": signed})
    signal_names = [identifiers[k] for k in ("clock", "valid", "ready") if k in identifiers]
    signal_names.extend(x["name"] for x in normalized_payload)
    if len(signal_names) != len(set(signal_names)):
        errors.append("clock, valid, ready, and payload signal names must all be unique.")
    source_ref = data.get("source_ref", "")
    if source_ref:
        if not isinstance(source_ref, str) or len(source_ref) > 1000 or "\n" in source_ref or "\r" in source_ref:
            errors.append("source_ref must be a single-line string of at most 1000 characters.")
    else:
        warnings.append("No source_ref supplied. The contract is user-provided and has not been checked against a controlled UCIe specification.")
    if errors:
        return data, errors, warnings
    normalized = dict(data)
    normalized["payload"] = normalized_payload
    return normalized, errors, warnings


def validate_ready_valid_contract(contract_json: str) -> dict[str, Any]:
    """Validate a user-supplied generic ready/valid contract; not UCIe compliance checking."""
    data, errors, warnings = _ready_valid_contract_data(contract_json)
    return {
        "status": "invalid" if errors else "valid", "errors": errors, "warnings": warnings,
        "interface_name": data.get("interface_name"), "agent_name": data.get("agent_name"),
        "role": data.get("role"),
        "payload_fields": len(data.get("payload", [])) if isinstance(data.get("payload"), list) else 0,
        "supported_contract": "single-clock generic ready/valid; no reset, timeout, packet framing, or UCIe-specific semantics",
        "disclaimer": "Structural validation only. The contract is not compared with the UCIe specification and does not establish FDI/RDI compliance.",
    }


def generate_ready_valid_uvm_agent(contract_json: str) -> dict[str, Any]:
    """Generate a generic source- or sink-side ready/valid interface and UVM agent."""
    data, errors, warnings = _ready_valid_contract_data(contract_json)
    if errors:
        raise ValueError("Invalid ready/valid contract: " + " ".join(errors))
    interface_name, agent_name = data["interface_name"], data["agent_name"]
    clock, valid, ready = data["clock"], data["valid"], data["ready"]
    role, payload = data["role"], data["payload"]
    drive_edge, sample_edge = data["drive_edge"], data["sample_edge"]
    payload_names = [x["name"] for x in payload]
    macro = chr(96)
    sigs = lambda items: ", ".join(items)
    payload_decls, payload_driver, payload_monitor, item_decls, item_macros = [], [], [], [], []
    for field in payload:
        width = field["width"]
        signed = " signed" if field["signed"] else ""
        packed = f" [{width - 1}:0]" if width > 1 else ""
        payload_decls.append(f"  logic{signed}{packed} {field['name']};")
        item_decls.append(f"    rand bit{signed}{packed} {field['name']};")
        item_macros.append(f"    {macro}uvm_field_int({field['name']}, UVM_DEFAULT)")
        payload_monitor.append(f"          observed.{field['name']} = vif.mon_cb.{field['name']};")
        if role == "source":
            payload_driver.append(f"        vif.drv_cb.{field['name']} <= req_item.{field['name']};")
    if role == "source":
        drv_out, drv_in, dut_in, dut_out = [valid] + payload_names, [ready], [valid] + payload_names, [ready]
        extra_decl, extra_macro = [], []
        driver_body = [
            "      @(vif.drv_cb);", f"      vif.drv_cb.{valid} <= 1'b0;", "      forever begin",
            "        seq_item_port.get_next_item(req_item);", "        @(vif.drv_cb);",
            f"        vif.drv_cb.{valid} <= 1'b1;", *payload_driver,
            "        do begin", "          @(vif.mon_cb);",
            f"        end while (vif.mon_cb.{ready} !== 1'b1);",
            "        @(vif.drv_cb);", f"        vif.drv_cb.{valid} <= 1'b0;",
            "        seq_item_port.item_done();", "      end"
        ]
    else:
        drv_out, drv_in, dut_in, dut_out = [ready], [valid] + payload_names, [ready], [valid] + payload_names
        extra_decl = ["    rand bit ready;"]
        extra_macro = [f"    {macro}uvm_field_int(ready, UVM_DEFAULT)"]
        driver_body = [
            "      @(vif.drv_cb);", f"      vif.drv_cb.{ready} <= 1'b0;", "      forever begin",
            "        seq_item_port.get_next_item(req_item);", "        @(vif.drv_cb);",
            f"        vif.drv_cb.{ready} <= req_item.ready;", "        @(vif.mon_cb);",
            "        seq_item_port.item_done();", "      end"
        ]
    assertion_lines = [
        "// SVA include fragment: place inside the generated interface or another module/interface scope.",
        f"property p_{agent_name}_valid_held_while_stalled;",
        f"  @({sample_edge} {clock}) ({valid} && !{ready}) |=> {valid};",
        "endproperty",
        f"assert property (p_{agent_name}_valid_held_while_stalled);",
    ]
    for field in payload:
        prop = f"p_{agent_name}_{field['name']}_stable_while_stalled"
        assertion_lines.extend([
            f"property {prop};",
            f"  @({sample_edge} {clock}) ({valid} && !{ready}) |=> $stable({field['name']});",
            "endproperty",
            f"assert property ({prop});",
        ])
    assertions_sv = "\n".join(assertion_lines) + "\n"
    interface_sv = "\n".join([
        "// Generic ready/valid interface generated from the supplied contract; verify before integration.",
        f"interface {interface_name}(input logic {clock});",
        f"  logic {valid};", f"  logic {ready};", *payload_decls, "",
        f"  clocking drv_cb @({drive_edge} {clock});", "    default input #1step output #0;",
        f"    output {sigs(drv_out)};", f"    input {sigs(drv_in)};", "  endclocking", "",
        f"  clocking mon_cb @({sample_edge} {clock});", "    default input #1step;",
        f"    input {sigs([valid, ready] + payload_names)};", "  endclocking", "",
        f"  modport dut (input {sigs([clock] + dut_in)}, output {sigs(dut_out)});",
        f"  modport tb (input {clock}, clocking drv_cb, clocking mon_cb);",
        f"endinterface : {interface_name}", ""
    ])
    item, sequencer, sequence = f"{agent_name}_item", f"{agent_name}_sequencer", f"{agent_name}_smoke_seq"
    driver, monitor, agent, package = f"{agent_name}_driver", f"{agent_name}_monitor", f"{agent_name}_agent", f"{agent_name}_agent_pkg"
    monitor_assignments = payload_monitor + ([f"          observed.ready = vif.mon_cb.{ready};"] if role == "sink" else [])
    package_lines = [
        "// Generic UVM ready/valid scaffold. Review timing and semantics against the real interface contract.",
        f"package {package};", "  import uvm_pkg::*;", f'  {macro}include "uvm_macros.svh"', "",
        f"  class {item} extends uvm_sequence_item;", *item_decls, *extra_decl,
        f"    {macro}uvm_object_utils_begin({item})", *item_macros, *extra_macro,
        f"    {macro}uvm_object_utils_end",
        f'    function new(string name = "{item}"); super.new(name); endfunction', "  endclass", "",
        f"  class {sequencer} extends uvm_sequencer #({item});", f"    {macro}uvm_component_utils({sequencer})",
        f'    function new(string name = "{sequencer}", uvm_component parent = null); super.new(name, parent); endfunction',
        "  endclass", "",
        f"  class {sequence} extends uvm_sequence #({item});", f"    {macro}uvm_object_utils({sequence})",
        f'    function new(string name = "{sequence}"); super.new(name); endfunction',
        "    task body();", f"      {item} req_item;", f'      req_item = {item}::type_id::create("req_item");',
        "      start_item(req_item);",
        f'      if (!req_item.randomize()) {macro}uvm_error("RAND", "Transaction randomization failed")',
        "      finish_item(req_item);", "    endtask", "  endclass", "",
        f"  class {driver} extends uvm_driver #({item});", f"    {macro}uvm_component_utils({driver})",
        f"    virtual {interface_name} vif;",
        f'    function new(string name = "{driver}", uvm_component parent = null); super.new(name, parent); endfunction',
        "    function void build_phase(uvm_phase phase);", "      super.build_phase(phase);",
        f'      if (!uvm_config_db #(virtual {interface_name})::get(this, "", "vif", vif))',
        f'        {macro}uvm_fatal("NOVIF", "Virtual interface not configured for {driver}")',
        "    endfunction", "    task run_phase(uvm_phase phase);", f"      {item} req_item;",
        *driver_body, "    endtask", "  endclass", "",
        f"  class {monitor} extends uvm_monitor;", f"    {macro}uvm_component_utils({monitor})",
        f"    virtual {interface_name} vif;", f"    uvm_analysis_port #({item}) analysis_port;",
        f'    function new(string name = "{monitor}", uvm_component parent = null);',
        "      super.new(name, parent);", '      analysis_port = new("analysis_port", this);', "    endfunction",
        "    function void build_phase(uvm_phase phase);", "      super.build_phase(phase);",
        f'      if (!uvm_config_db #(virtual {interface_name})::get(this, "", "vif", vif))',
        f'        {macro}uvm_fatal("NOVIF", "Virtual interface not configured for {monitor}")',
        "    endfunction", "    task run_phase(uvm_phase phase);", f"      {item} observed;",
        "      forever begin", "        @(vif.mon_cb);",
        f"        if ((vif.mon_cb.{valid} === 1'b1) && (vif.mon_cb.{ready} === 1'b1)) begin",
        f'          observed = {item}::type_id::create("observed");', *monitor_assignments,
        "          analysis_port.write(observed);", "        end", "      end", "    endtask", "  endclass", "",
        f"  class {agent} extends uvm_agent;", f"    {macro}uvm_component_utils({agent})",
        f"    virtual {interface_name} vif;", f"    {monitor} monitor;", f"    {driver} driver;", f"    {sequencer} sequencer;",
        f'    function new(string name = "{agent}", uvm_component parent = null); super.new(name, parent); endfunction',
        "    function void build_phase(uvm_phase phase);", "      super.build_phase(phase);",
        f'      if (!uvm_config_db #(virtual {interface_name})::get(this, "", "vif", vif))',
        f'        {macro}uvm_fatal("NOVIF", "Virtual interface not configured for {agent}")',
        f'      uvm_config_db #(virtual {interface_name})::set(this, "monitor", "vif", vif);',
        f'      monitor = {monitor}::type_id::create("monitor", this);', "      if (is_active == UVM_ACTIVE) begin",
        f'        uvm_config_db #(virtual {interface_name})::set(this, "driver", "vif", vif);',
        f'        driver = {driver}::type_id::create("driver", this);',
        f'        sequencer = {sequencer}::type_id::create("sequencer", this);', "      end",
        "    endfunction", "    function void connect_phase(uvm_phase phase);", "      super.connect_phase(phase);",
        "      if (is_active == UVM_ACTIVE) driver.seq_item_port.connect(sequencer.seq_item_export);",
        "    endfunction", "  endclass", "", f"endpackage : {package}", ""
    ]
    return {
        "status": "generated", "interface_name": interface_name, "agent_name": agent_name, "role": role,
        "interface_file": f"{interface_name}.sv", "interface_sv": interface_sv,
        "package_file": f"{package}.sv", "package_sv": "\n".join(package_lines),
        "assertions_file": f"{agent_name}_contract_assertions.svh", "assertions_sv": assertions_sv,
        "warnings": warnings, "source_ref": data.get("source_ref") or None,
        "limitations": [
            "Generic single-clock ready/valid scaffold only; not a UCIe FDI/RDI implementation.",
            "Reset, timeout, packet framing, CRC, retry/replay, credits, and protocol-specific ordering are not generated.",
            "Compile the interface before the UVM package and configure the virtual interface from the testbench.",
            "Generated SystemVerilog has not been compiled or simulated by this tool."
        ]
    }


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
