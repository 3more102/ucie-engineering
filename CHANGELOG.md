# Changelog

## 1.3.4 — 2026-11-17

- Added a Slang compile/type-check of both generated source and sink agents against the pinned Accellera UVM 2020.3.1 reference library.
- CI checks actual UVM class APIs, factory macros, virtual-interface configuration, sequencer/driver connections, and generated package elaboration; no simulator execution is claimed.
- Pinned the UVM reference source to commit `78c06547a2a0a29b3dc9dcafae62b75b2ff61544` for reproducible validation.
- Bumped MCP package and bundle version to 1.3.4.


## 1.3.3 — 2026-11-17

- Corrected sink-agent idle behavior: poll `try_next_item` at each drive edge and explicitly deassert ready when no sequence item is available.
- Changed transaction-randomization failure from a recoverable UVM error to a fatal error so invalid stimulus is not sent.
- Added generated-code syntax validation using the Slang SystemVerilog frontend for source/sink interfaces, SVA fragments, and UVM package syntax with macro stubs.
- Added CI checks and regression tests for sink backpressure idle behavior.
- Bumped MCP package and bundle version to 1.3.3.


## 1.3.2 — 2026-11-16

- Hardened the release source archive to include only files committed in the Git tree, excluding untracked workspace files such as local `.env` files.
- Added a regression test using a temporary Git repository containing tracked files, an untracked `.env`, and untracked notes.
- Aligned the MCP runtime server version with the manifest and Python package; added a CI metadata-consistency regression test.
- Bumped MCP package and bundle version to 1.3.2.


## 1.3.1 — 2026-11-16

- Fixed source/sink UVM generation to use the contract's actual valid, ready, clock, and payload signal names rather than default names.
- Added regression tests for custom signal names in both agent roles.
- Bumped MCP package and bundle version to 1.3.1.


## 1.3.0 — 2026-11-16

- Added explicit generic ready/valid contract validation for source and sink roles.
- Added generation of SystemVerilog interfaces with separate drive/monitor clocking blocks and DUT/testbench modports.
- Added contract-driven UVM source/sink agents with transaction, smoke sequence, sequencer, driver, monitor, and analysis port.
- Added SVA include fragments for valid persistence and payload stability after a sampled stall.
- Added regression tests for source/sink directionality, clock-edge separation, duplicate signals, source-reference warnings, and unsupported reset declarations.
- Documented the limits of generated scaffolding and the need for project-specific reset and protocol behavior.
- Bumped MCP package and bundle version to 1.3.0.


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
