# Contributing

## Engineering principles

- Keep normative claims tied to an exact UCIe revision and source location.
- Do not include proprietary standards text or confidential project data.
- Preserve the separation between Protocol Layer, Adapter, and PHY responsibilities.
- Keep generated RTL declaration-only unless the required behavior is source-backed.
- Add tests for every utility behavior and invalid-input path.
- Keep the MCP server local STDIO unless a separately reviewed security design approves another transport.

## Development

~~~bash
cd mcp-server
python -m unittest discover -s tests -v
python -m compileall -q ucie_mcp
~~~

If the MCP SDK is installed:

~~~bash
uv run mcp dev ucie_mcp/server.py
~~~

## Pull requests

Include the problem statement, scope, source/revision impact, tests executed, limitations, and any changes to the manifest or tool schema. Do not describe a draft, simulation, or field-completeness result as UCIe compliance.
