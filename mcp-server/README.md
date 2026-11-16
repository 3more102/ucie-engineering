# UCIe Engineering MCP Server

Local STDIO MCP server exposing deterministic UCIe workflow helpers. Requires Python 3.11+ and uv.

~~~bash
uv sync
uv run ucie-mcp
~~~

The process waits for an MCP client over STDIO. Do not print startup messages to stdout; stdout is reserved for the protocol stream.

Run core tests without installing the MCP SDK:

~~~bash
python -m unittest discover -s tests -v
~~~

Run the MCP Inspector after installing the CLI extra:

~~~bash
uv run mcp dev ucie_mcp/server.py
~~~

The server has no filesystem, shell, or network tools. See ../docs/SECURITY.md.
