# Changelog

## 1.2.0 — 2026-11-16

- Added UVM agent class scaffolding for transaction, sequence, sequencer, driver, monitor, and agent.
- Added regression coverage for generated class structure and duplicate transaction-field rejection.
- Bumped MCP package and bundle version to 1.2.0.


## 1.1.0 — 2026-11-16

- Added explicit overlapped/non-overlapped SVA implication selection.
- Added generic ready/valid hold assertions using next-sample semantics.
- Fixed MCP Inspector direct-file import mode.
- Recompute SHA-256 checksums after official MCPB packaging in CI.
- Added regression tests for temporal operator selection and ready/valid hold properties.
- Bumped MCP package and bundle version to 1.1.0.

## 1.0.0 — 2026-11-16

- Initial UCIe Engineering Claude Skill and local MCP server.
- Added architecture, source hierarchy, verification, RTL-to-GDSII, and publication guidance.
- Added manifest validation, architecture completeness review, SV/SVA scaffolding, UVM test-plan drafting, traceability audit, and generic CRC-16/CCITT-FALSE helper.
- Added example manifests, tests, installation documentation, and MCPB manifest.
- Explicitly documented that generated outputs and helper checks do not establish UCIe compliance.
