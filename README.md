# UCIe Engineering — Claude Skill + MCP

A source-grounded engineering assistant for UCIe die-to-die adapter architecture, RTL design, verification, FPGA/ASIC implementation planning, and research workflows.

## Repository layout

- skill/ucie-engineering/SKILL.md — Claude Agent Skill instructions.
- skill/ucie-engineering/references/ — architecture, verification, source control, implementation, and publication guidance.
- mcp-server/ — local Python MCP server and deterministic engineering utilities.
- docs/ — installation and security guidance.
- scripts/build_release.py — creates the uploadable Skill ZIP, MCPB bundle, source archive, and initial SHA-256 manifest.
- scripts/write_checksums.py — recomputes checksums after final MCPB packaging.

## Baseline policy

The example project profile uses UCIe 3.0 as a controlled starting baseline. UCIe 4.0 is treated as a separate revision; requirements must never be mixed across revisions without an approved migration. The example profile is not a claim that UCIe 3.0 is the newest available specification.

Normative source hierarchy:
1. Authorized UCIe specification revision and applicable ECNs.
2. Official UCIe Consortium publications.
3. Applicable Accellera standards and reference materials.
4. Peer-reviewed papers and vendor technical documentation.
5. Community implementations as non-normative references.

Official links:
- UCIe specifications: https://www.uciexpress.org/specifications
- UCIe Consortium publications: https://www.uciexpress.org/press-releases
- Official MCP Python SDK: https://py.sdk.modelcontextprotocol.io/
- MCP Bundles: https://github.com/modelcontextprotocol/mcpb

## Engineering guardrails

- Cite exact revision, section, table/figure, and page for normative claims.
- Distinguish specification requirements, project requirements, design decisions, assumptions, and unverified claims.
- Keep Protocol Layer, Die-to-Die Adapter, and Physical Layer responsibilities separate.
- Treat FDI and RDI as distinct interface contracts.
- Do not claim standards compliance from generated RTL, lint, unit tests, or a partial simulation.
- The generic CRC-16/CCITT-FALSE utility is not a UCIe CRC implementation.
- The generic ready/valid SVA helper is a contract template, not a UCIe-specific interface definition. The UVM agent generator creates class scaffolding only; pin-driving and monitor sampling must be implemented from the verified interface contract.
- Do not reproduce copyrighted specification text; use an authorized copy and cite precise locations.

## Build release artifacts

Requirements: Python 3.11+.

~~~bash
python scripts/build_release.py
~~~

The command creates:
- dist/ucie-engineering-skill.zip — uploadable Claude Agent Skill.
- dist/ucie-engineering.mcpb — MCP bundle staging archive.
- dist/ucie-claude-engineering-source.zip — editable source archive.
- dist/SHA256SUMS.txt — checksums for the artifacts produced by the builder.

For a final distribution package, validate and repack the MCPB with the official CLI, then refresh the checksums:

~~~bash
mcpb validate mcp-server/manifest.json
mcpb pack mcp-server dist/ucie-engineering.mcpb
python scripts/write_checksums.py
~~~

CI performs these steps in this order and uploads the final packages as a workflow artifact. Attach validated packages to a GitHub Release after review.

## Install

### Claude Agent Skill
Upload dist/ucie-engineering-skill.zip in Claude's Skills settings and enable it. See [Installation](docs/INSTALLATION.md).

### Claude Desktop MCP Bundle
Install dist/ucie-engineering.mcpb through the Extensions / Advanced installation flow in Claude Desktop. Validate the bundle with the official MCPB CLI and test it on the target Desktop version.

### Local MCP development
Requirements: Python 3.11+ and uv.

~~~bash
cd mcp-server
uv sync
uv run ucie-mcp
python -m unittest discover -s tests -v
~~~

## MCP tools

- ucie_validate_project_manifest
- ucie_review_architecture_inputs
- ucie_generate_sv_module_shell
- ucie_generate_sva_skeleton — explicit overlapped/non-overlapped implication.
- ucie_generate_ready_valid_sva — generic next-cycle valid/payload hold assertions.
- ucie_generate_uvm_agent_skeleton — basic UVM class shells.
- ucie_validate_ready_valid_contract — validate an explicit generic ready/valid contract.
- ucie_generate_ready_valid_uvm_agent — generate source/sink interface and UVM agent files from that contract.
- ucie_generate_uvm_testplan
- ucie_audit_traceability_matrix
- ucie_crc16_ccitt_false

The tools are deterministic drafting and audit utilities. They do not inspect project files, execute simulators, synthesize RTL, or certify UCIe compliance.

## Validation status

GitHub Actions validates Python 3.11, 3.12, and 3.13, runs unit tests, compiles Python sources, validates JSON inputs, checks MCPB packaging, and smoke-tests both package import and the direct-file import path used by MCP Inspector. The workflow artifact is named ucie-engineering-v1.3.0.

## License

MIT. See [LICENSE](LICENSE). UCIe specifications and third-party materials are not included and remain subject to their respective terms.
