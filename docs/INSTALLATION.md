# Installation and operation

## Claude Agent Skill

The Skill is the knowledge and workflow layer. Build the uploadable archive with:

~~~bash
python scripts/build_release.py
~~~

Upload dist/ucie-engineering-skill.zip in Claude's Skills interface and enable it. The Skill can operate without the MCP server.

Official guide: https://support.claude.com/en/articles/12512198-how-to-create-custom-skills

## Claude Desktop MCP Bundle

Build dist/ucie-engineering.mcpb with the same command. In Claude Desktop, open Settings and the Extensions / Developer / Advanced installation area available in your installed version, then install the local MCPB file.

Official MCP Bundles project: https://github.com/modelcontextprotocol/mcpb

The bundle uses the MCPB 0.4 manifest and UV-managed runtime. Validate with the official MCPB CLI and test on the target Claude Desktop version before production deployment.

## Manual local MCP setup

Requirements: Python 3.11+ and uv.

~~~bash
cd mcp-server
uv sync
uv run ucie-mcp
~~~

For Claude Desktop, merge mcp-server/config/claude_desktop_config.example.json into the local configuration and replace the example path with the absolute path to mcp-server.

For Claude Code, copy mcp-server/config/.mcp.json.example to the project root as .mcp.json and update the absolute path. Do not commit machine-specific paths or secrets.

## Verification

1. Run python -m unittest discover -s tests -v from mcp-server.
2. Run uv run mcp dev ucie_mcp/server.py to inspect tool schemas.
3. Call every tool with valid and invalid inputs.
4. Verify that stdout contains only MCP protocol messages.
5. Install the MCPB in the target Claude Desktop build.
