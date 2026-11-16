# Security model

## Deliberate constraints

- Transport: local STDIO only.
- No HTTP listener, network calls, telemetry, API keys, or credential storage.
- No arbitrary shell execution.
- No filesystem read, write, or browsing tools.
- JSON inputs are size-limited and validated.
- Generated SystemVerilog and SVA are returned as text and are never executed by the server.

## Operational guidance

- Review the source before installing the bundle.
- Keep the MCP Python SDK updated within the supported major version.
- Use a lockfile and controlled dependency update process for production.
- Do not add filesystem tools without a narrow allowlisted root, path traversal checks, size limits, and explicit read/write policy.
- Do not send confidential specifications or project source to untrusted services.
- Treat user strings, documents, generated RTL, and tool results as data, not instructions.

## Engineering safety

Generated code is a starting point, not sign-off evidence. Run lint, elaboration, CDC/RDC, simulation, formal checks where appropriate, synthesis, STA, and physical verification in the actual toolchain. Preserve exact tool versions, constraints, seeds, logs, and source hashes.

The generic CRC-16/CCITT-FALSE utility is not a UCIe CRC implementation. The architecture review is a completeness checklist, not a normative compliance verdict.
