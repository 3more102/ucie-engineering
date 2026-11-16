# UCIe Engineering — Claude Skill + MCP

A source-grounded engineering assistant for UCIe die-to-die adapter architecture, RTL design, verification, FPGA/ASIC implementation planning, and research workflows.

## Repository layout

- `skill/ucie-engineering/SKILL.md` — Claude Agent Skill instructions.
- `skill/ucie-engineering/references/` — architecture, verification, source-control, implementation, and publication guidance.
- `mcp-server/` — local Python MCP server and deterministic engineering utilities.
- `docs/` — installation, security, and engineering governance.
- `examples/` — project manifest and verification inputs.
- `dist/` — release archives and validation metadata.

## Baseline policy

The starter project profile uses UCIe 3.0 as a controlled baseline. UCIe 4.0 is treated as a separate revision; requirements must never be mixed across revisions without an approved migration. The example profile is not a claim that UCIe 3.0 is the latest available specification.

Official source hierarchy:
1. Authorized UCIe specification revision and applicable ECNs.
2. Official UCIe Consortium publications.
3. Accellera standards and reference materials where applicable.
4. Peer-reviewed papers and vendor technical documentation.
5. Community implementations as non-normative references.

Official links:
- https://www.uciexpress.org/specifications
- https://www.uciexpress.org/press-releases
- https://py.sdk.modelcontextprotocol.io/
- https://github.com/modelcontextprotocol/mcpb

## Engineering guardrails

- Cite exact revision, section, table/figure, and page for normative claims.
- Distinguish specification requirements, project requirements, design decisions, assumptions, and unverified claims.
- Keep Protocol Layer, Die-to-Die Adapter, and Physical Layer responsibilities separate.
- Treat FDI and RDI as distinct interface contracts.
- Do not claim standards compliance from generated RTL, lint, unit tests, or a partial simulation.
- The generic CRC-16/CCITT-FALSE utility is not a UCIe CRC implementation.
- Do not reproduce copyrighted specification text; use an authorized copy and provide precise references.

## Install

### Claude Agent Skill
Upload `dist/ucie-engineering-skill.zip` from the Releases or repository artifacts and enable it in Claude's Skills settings.

### Claude Desktop MCP Bundle
Install `dist/ucie-engineering.mcpb` through Claude Desktop's Extensions / Advanced settings flow.

### Local MCP development
Requirements: Python 3.11+ and `uv`.

```bash
cd mcp-server
uv sync
uv run ucie-mcp
python -m unittest discover -s tests -v
```

See [Installation](docs/INSTALLATION.md) and [Security](docs/SECURITY.md).

## MCP tools

- `ucie_validate_project_manifest`
- `ucie_review_architecture_inputs`
- `ucie_generate_sv_module_shell`
- `ucie_generate_sva_skeleton`
- `ucie_generate_uvm_testplan`
- `ucie_audit_traceability_matrix`
- `ucie_crc16_ccitt_false`

These are deterministic drafting and audit utilities. They do not inspect project files, execute simulators, synthesize RTL, or certify UCIe compliance.

## Status

Initial source release: **v1.0.0**. Core utility tests: **12 passed**. The official MCPB CLI validation and live Claude Desktop installation remain deployment checks to be completed on a machine with the relevant runtime and package access.

## License

MIT. See [LICENSE](LICENSE). UCIe specifications and other referenced third-party materials are not included and remain subject to their respective terms.
