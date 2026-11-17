"""UCIe Engineering MCP server. STDIO is reserved for MCP protocol traffic."""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

from mcp.server import MCPServer

# The MCP Inspector loads this file directly with importlib, without package
# context. Add the package root only in that direct-file execution mode.
if __package__:
    from . import core
else:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from ucie_mcp import core

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ucie-engineering")
mcp = MCPServer("ucie-engineering", version="1.3.4")


def _json_result(function, *args):
    try:
        return json.dumps(function(*args), indent=2, ensure_ascii=False)
    except (ValueError, TypeError) as exc:
        return json.dumps({"status": "error", "error": str(exc)}, indent=2, ensure_ascii=False)


@mcp.tool()
def ucie_validate_project_manifest(manifest_json: str) -> str:
    """Validate the structure and source/scope fields of a UCIe project manifest; does not verify source claims."""
    return _json_result(core.validate_project_manifest, manifest_json)


@mcp.tool()
def ucie_review_architecture_inputs(architecture_json: str) -> str:
    """Find missing architecture review inputs; this is not a normative compliance checker."""
    return _json_result(core.review_architecture_inputs, architecture_json)


@mcp.tool()
def ucie_generate_sv_module_shell(module_name: str, ports_json: str) -> str:
    """Generate a declaration-only SystemVerilog module shell from a supplied JSON port array."""
    try:
        return core.generate_sv_module_shell(module_name, ports_json)
    except (ValueError, TypeError) as exc:
        return json.dumps({"status": "error", "error": str(exc)}, indent=2)


@mcp.tool()
def ucie_generate_sva_skeleton(
    property_name: str,
    clock: str,
    antecedent: str,
    consequent: str,
    disable_iff: str = "",
    implication: str = "|->",
) -> str:
    """Generate an SVA skeleton using overlapped |-> or non-overlapped |=> implication."""
    try:
        return core.generate_sva_skeleton(
            property_name, clock, antecedent, consequent, disable_iff, implication
        )
    except (ValueError, TypeError) as exc:
        return json.dumps({"status": "error", "error": str(exc)}, indent=2)


@mcp.tool()
def ucie_generate_ready_valid_sva(
    prefix: str,
    clock: str,
    valid: str,
    ready: str,
    payload: str,
    disable_iff: str = "",
) -> str:
    """Generate generic ready/valid hold assertions; this is not a UCIe interface definition."""
    try:
        return core.generate_ready_valid_sva(prefix, clock, valid, ready, payload, disable_iff)
    except (ValueError, TypeError) as exc:
        return json.dumps({"status": "error", "error": str(exc)}, indent=2)



@mcp.tool()
def ucie_generate_uvm_agent_skeleton(agent_name: str, interface_type: str, fields_json: str) -> str:
    """Generate UVM transaction, sequence, sequencer, driver, monitor, and agent class shells."""
    try:
        return core.generate_uvm_agent_skeleton(agent_name, interface_type, fields_json)
    except (ValueError, TypeError) as exc:
        return json.dumps({"status": "error", "error": str(exc)}, indent=2)


@mcp.tool()
def ucie_validate_ready_valid_contract(contract_json: str) -> str:
    """Validate an explicit generic ready/valid contract; not a UCIe compliance check."""
    return _json_result(core.validate_ready_valid_contract, contract_json)


@mcp.tool()
def ucie_generate_ready_valid_uvm_agent(contract_json: str) -> str:
    """Generate a generic source- or sink-side ready/valid interface and UVM agent."""
    return _json_result(core.generate_ready_valid_uvm_agent, contract_json)


@mcp.tool()
def ucie_generate_uvm_testplan(features_json: str, scope_note: str = "") -> str:
    """Draft a UVM plan from explicit feature records; missing requirements and expected behavior remain TODOs."""
    try:
        return core.generate_uvm_testplan(features_json, scope_note)
    except (ValueError, TypeError) as exc:
        return json.dumps({"status": "error", "error": str(exc)}, indent=2)


@mcp.tool()
def ucie_audit_traceability_matrix(rows_json: str) -> str:
    """Audit requirement-to-design-to-test traceability fields; does not open evidence files."""
    return _json_result(core.audit_traceability_matrix, rows_json)


@mcp.tool()
def ucie_crc16_ccitt_false(data_hex: str) -> str:
    """Calculate generic CRC-16/CCITT-FALSE; this is not a UCIe-specific CRC implementation."""
    return _json_result(core.crc16_ccitt_false, data_hex)


@mcp.resource("ucie://guide/engineering-principles")
def engineering_principles() -> str:
    """Core source-grounding and verification principles."""
    return (
        "Freeze the exact UCIe revision and scope before normative claims. "
        "Cite exact source locations; never invent bit fields, timing, CRC parameters, or state behavior. "
        "Keep Protocol Layer, Adapter, and PHY responsibilities distinct. "
        "Define FDI and RDI contracts independently. "
        "Derive tests, assertions, and coverage from atomic requirements. "
        "Generated code is not compliance evidence. This server does not inspect files, run EDA tools, or certify compliance."
    )


@mcp.prompt()
def start_ucie_adapter_review(project_name: str, baseline: str = "user-specified") -> str:
    """Create a structured, source-grounded UCIe adapter architecture review prompt."""
    return (
        f"Review UCIe adapter project {project_name}. Declared baseline: {baseline}. "
        "First identify the exact authorized specification revision. Review scope, Protocol/Adapter/PHY boundaries, "
        "FDI and RDI contracts, mainband/sideband, reliability, replay/buffering, credits, reset/clock/power, "
        "verification, and ASIC/FPGA implementation. Separate requirements from assumptions and decisions. "
        "Cite exact source locations. Do not invent values or claim compliance without evidence. "
        "Return open questions and prioritized exit criteria."
    )


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
