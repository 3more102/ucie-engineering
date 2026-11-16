# UCIe Engineering MCP Server

Local STDIO MCP server exposing deterministic UCIe workflow helpers, including contract-driven generic ready/valid UVM agent generation. Version 1.3.2. Requires Python 3.11+ and uv.

~~~bash
uv sync
uv run ucie-mcp
~~~

The process waits for an MCP client over STDIO. Do not print startup messages to stdout; stdout is reserved for the protocol stream.

## Contract-driven ready/valid agent generation

Provide an explicit JSON contract based on your approved interface definition. The contract must name the interface, agent, clock, distinct drive/sample edges, source/sink role, valid/ready signals, and payload fields with widths. A source example is:

~~~json
{
  "schema_version": "1.0",
  "interface_name": "fdi_tx_if",
  "agent_name": "fdi_tx",
  "clock": "clk",
  "drive_edge": "negedge",
  "sample_edge": "posedge",
  "role": "source",
  "valid": "valid",
  "ready": "ready",
  "payload": [{"name": "flit", "width": 128}],
  "source_ref": "Replace with approved contract revision and clause"
}
~~~

The validator checks structure. The generator returns a SystemVerilog interface, a UVM package, and an SVA include fragment checking valid persistence and per-field payload stability after a sampled stall. Source agents drive valid/payload while waiting for ready; sink agents drive ready and monitor incoming payload. Reset, timeout, packet framing, CRC, retry/replay, credits, and UCIe-specific FDI/RDI behavior are not generated. Review, compile, and simulate generated code before integration.

Run core tests:

~~~bash
python -m unittest discover -s tests -v
~~~

Run the MCP Inspector from the mcp-server directory:

~~~bash
uv run mcp dev ucie_mcp/server.py
~~~

The server supports direct-file loading by the Inspector as well as normal package entry-point execution. It has no filesystem, shell, or network tools. See ../docs/SECURITY.md.
