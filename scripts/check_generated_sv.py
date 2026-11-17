#!/usr/bin/env python3
"""Parse and elaborate generated ready/valid interfaces and SVA with Slang.

The UVM package is syntax-parsed with minimal macro stubs only. This does not
claim semantic compatibility with a vendor UVM library or simulation sign-off.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "mcp-server"))

from ucie_mcp import core  # noqa: E402
from pyslang import DiagnosticEngine  # noqa: E402
from pyslang.ast import Compilation  # noqa: E402
from pyslang.syntax import SyntaxTree  # noqa: E402

TICK = chr(96)
UVM_MACRO_STUBS = "\n".join([
    TICK + "define uvm_object_utils_begin(T)",
    TICK + "define uvm_field_int(F, FLAGS)",
    TICK + "define uvm_object_utils_end",
    TICK + "define uvm_component_utils(T)",
    TICK + "define uvm_object_utils(T)",
    TICK + "define uvm_error(ID, MSG) $error(MSG);",
    TICK + "define uvm_fatal(ID, MSG) $fatal(1, MSG);",
])

def contract(role: str) -> dict:
    return {
        "schema_version": "1.0",
        "interface_name": f"ci_{role}_if",
        "agent_name": f"ci_{role}",
        "clock": "link_clk",
        "drive_edge": "negedge",
        "sample_edge": "posedge",
        "role": role,
        "valid": f"{role}_valid",
        "ready": f"{role}_ready",
        "payload": [
            {"name": f"{role}_flit", "width": 128},
            {"name": f"{role}_opcode", "width": 4},
            {"name": f"{role}_signed_meta", "width": 7, "signed": True},
        ],
        "source_ref": "CI fixture only; not a UCIe specification claim",
    }

def fail_with_diagnostics(label: str, source_manager, diagnostics) -> None:
    report = DiagnosticEngine.reportAll(source_manager, diagnostics)
    raise RuntimeError(f"{label} failed:\n{report}")

def check_interface_and_assertions(role: str, generated: dict) -> None:
    interface = generated["interface_sv"]
    marker = f"endinterface : {generated['interface_name']}"
    if marker not in interface:
        raise RuntimeError(f"{role}: generated interface terminator is missing")
    combined = interface.replace(marker, generated["assertions_sv"] + "\n" + marker)
    tree = SyntaxTree.fromText(combined)
    if tree.diagnostics:
        raise RuntimeError(f"{role}: Slang parser diagnostics: {tree.diagnostics}")
    compilation = Compilation()
    compilation.addSyntaxTree(tree)
    diagnostics = compilation.getAllDiagnostics()
    if compilation.hasIssuedErrors():
        fail_with_diagnostics(f"{role} interface + SVA", compilation.sourceManager, diagnostics)

def check_uvm_package_syntax(role: str, generated: dict) -> None:
    package_source = generated["package_sv"].replace(
        TICK + 'include "uvm_macros.svh"', UVM_MACRO_STUBS
    )
    tree = SyntaxTree.fromText(package_source)
    if tree.diagnostics:
        raise RuntimeError(f"{role}: UVM package parser diagnostics: {tree.diagnostics}")

def main() -> int:
    for role in ("source", "sink"):
        generated = core.generate_ready_valid_uvm_agent(json.dumps(contract(role)))
        check_interface_and_assertions(role, generated)
        check_uvm_package_syntax(role, generated)
    print(
        "Slang validation passed for source/sink interfaces and SVA; "
        "UVM packages passed syntax parsing with macro stubs only."
    )
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"generated SystemVerilog validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
