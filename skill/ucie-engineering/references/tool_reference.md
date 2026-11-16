# MCP tool reference

The MCP server provides deterministic drafting and audit utilities. It does not read the UCIe specification, inspect local project files, execute simulators, synthesize RTL, or verify that evidence paths exist.

## Manifest validation

Tool: ucie_validate_project_manifest

Input: JSON string with schema_version, project, baseline, scope, interfaces, and verification. Returns structural errors and warnings. A valid result does not verify the truth of source claims.

## Architecture review

Tool: ucie_review_architecture_inputs

Input: JSON object with baseline, scope, interfaces, mainband_sideband, reliability, flow_control, power_reset, verification, and implementation categories. Reports populated/missing review fields. Missing fields are not standards violations.

## SystemVerilog shell

Tool: ucie_generate_sv_module_shell

Inputs: module_name and ports_json. Port records require name and direction (input/output/inout); optional width and signed. Generates declarations only and does not infer functional behavior.

## SVA skeleton

Tool: ucie_generate_sva_skeleton

Inputs: property_name, clock, antecedent, consequent, optional disable_iff, and implication. The implication is either |-> (overlapped, same sampled cycle) or |=> (non-overlapped, next sampled cycle). Use |=> when the intended check begins on the following clock, such as checking that a stalled ready/valid payload remains stable into the next sample. Confirm the temporal behavior against the interface contract.

## Generic ready/valid assertions

Tool: ucie_generate_ready_valid_sva

Inputs: prefix, clock, valid, ready, payload, and optional disable_iff. Generates two generic assertions: valid remains asserted after a sampled valid && !ready stall, and payload is stable at the next sample. This is a reusable ready/valid contract template, not a UCIe FDI/RDI definition or normative UCIe requirement. Confirm the interface semantics before use.

## UVM agent scaffold

Tool: ucie_generate_uvm_agent_skeleton

Inputs: agent_name, interface_type, and fields_json. Generates transaction, smoke sequence, sequencer, driver, monitor, and agent class shells, plus virtual-interface configuration plumbing. The field model is limited to simple integral fields with explicit widths. Driver pin-driving and monitor sampling are TODOs; this is not a complete or compiled UVM environment. The interface type and semantics must be supplied and verified by the project.

## UVM test plan

Tool: ucie_generate_uvm_testplan

Input: features_json array. Records may include id, name, source_refs, requirement, nominal_stimulus, expected_result, boundary_cases, negative_cases, and coverage_points. Missing details remain TODOs.

## Traceability audit

Tool: ucie_audit_traceability_matrix

Input: rows_json array with requirement_id, source_ref, design_ref, test_id, result, and evidence_ref. FAIL rows should include issue_ref. The tool checks fields only and does not open evidence.

## CRC reference

Tool: ucie_crc16_ccitt_false

Calculates generic CRC-16/CCITT-FALSE: width 16, polynomial 0x1021, initial value 0xFFFF, refin/refout false, xorout 0x0000. The check vector ASCII 123456789 yields 0x29B1. This is not a UCIe-specific CRC implementation.


## Contract-driven generic ready/valid UVM agent

Tools:
- ucie_validate_ready_valid_contract
- ucie_generate_ready_valid_uvm_agent

Input is one JSON contract containing schema_version, interface_name, agent_name, clock, drive_edge, sample_edge, role (source or sink), valid, ready, payload fields (name, width, optional signed), and optional source_ref.

The validator checks identifiers, unique signal names, payload widths, role, and distinct drive/sample edges. A missing source_ref is a warning. The generator returns two source files: a SystemVerilog interface with clocking blocks and modports, and a UVM package containing a transaction, one-item smoke sequence, sequencer, driver, monitor, and agent. A source agent drives valid and payload while waiting for ready; a sink agent drives ready according to sequence items. The monitor publishes observed payload transactions on valid && ready.

This is a generic single-clock ready/valid template, not a UCIe FDI/RDI implementation. Reset handling, timeout policy, packet framing, CRC, retry/replay, credits, ordering, and protocol-specific semantics are not generated. The helper rejects a non-empty reset declaration rather than silently ignoring it. The generated SystemVerilog is not compiled or simulated by the tool. Compile the interface before the package, configure the virtual interface from the testbench, and review all behavior against the controlled project contract before integration.
