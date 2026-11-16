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

Inputs: property_name, clock, antecedent, consequent, and optional disable_iff. Expressions must be taken from the verified design contract. Output is a starting point, not a proof.

## UVM test plan

Tool: ucie_generate_uvm_testplan

Input: features_json array. Records may include id, name, source_refs, requirement, nominal_stimulus, expected_result, boundary_cases, negative_cases, and coverage_points. Missing details remain TODOs.

## Traceability audit

Tool: ucie_audit_traceability_matrix

Input: rows_json array with requirement_id, source_ref, design_ref, test_id, result, and evidence_ref. FAIL rows should include issue_ref. The tool checks fields only and does not open evidence.

## CRC reference

Tool: ucie_crc16_ccitt_false

Calculates generic CRC-16/CCITT-FALSE: width 16, polynomial 0x1021, initial value 0xFFFF, refin/refout false, xorout 0x0000. The check vector ASCII 123456789 yields 0x29B1. This is not a UCIe-specific CRC implementation.
