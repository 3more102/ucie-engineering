# UCIe Engineering MCP Server

Local STDIO MCP server exposing deterministic UCIe workflow helpers. Version 1.1.0. Requires Python 3.11+ and uv.

~~~bash
uv sync
uv run ucie-mcp
~~~

The process waits for an MCP client over STDIO. Do not print startup messages to stdout; stdout is reserved for the protocol stream.

Run core tests:

~~~bash
python -m unittest discover -s tests -v
~~~

Run the MCP Inspector from the mcp-server directory:

~~~bash
uv run mcp dev ucie_mcp/server.py
~~~

The server supports direct-file loading by the Inspector as well as normal package entry-point execution. It has no filesystem, shell, or network tools. See ../docs/SECURITY.md.
