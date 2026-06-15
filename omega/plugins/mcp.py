from __future__ import annotations

import asyncio
import json
from typing import Any

from omega.plugins.base import Plugin, PluginContext
from omega.schema import PluginResult


def _frame(payload: dict[str, Any]) -> bytes:
    body = json.dumps(payload).encode("utf-8")
    return f"Content-Length: {len(body)}\r\n\r\n".encode("ascii") + body


async def _read_frame(reader: asyncio.StreamReader) -> dict[str, Any]:
    headers = b""
    while b"\r\n\r\n" not in headers:
        chunk = await reader.read(1)
        if not chunk:
            raise RuntimeError("MCP server closed stdout before responding.")
        headers += chunk
    header_text, rest = headers.split(b"\r\n\r\n", 1)
    length = 0
    for line in header_text.decode("ascii").split("\r\n"):
        if line.lower().startswith("content-length:"):
            length = int(line.split(":", 1)[1].strip())
    body = rest + await reader.readexactly(length - len(rest))
    return json.loads(body.decode("utf-8"))


class MCPPlugin(Plugin):
    name = "mcp"
    description = "Discover configured MCP servers and list their tools through stdio JSON-RPC."
    actions = {
        "list_servers": "List configured MCP servers.",
        "list_tools": "Start a configured stdio MCP server and list tools.",
    }

    async def call(self, action: str, arguments: dict[str, Any], context: PluginContext) -> PluginResult:
        config_path = context.settings.mcp_config_path
        if not config_path.exists():
            return PluginResult(plugin=self.name, action=action, ok=True, data={"servers": {}})
        config = json.loads(config_path.read_text(encoding="utf-8"))
        servers = config.get("servers", {})
        if action == "list_servers":
            return PluginResult(plugin=self.name, action=action, ok=True, data={"servers": servers})
        if action == "list_tools":
            name = str(arguments["server"])
            server = servers.get(name)
            if not server:
                return PluginResult(plugin=self.name, action=action, ok=False, error=f"MCP server '{name}' is not configured.")
            command = server["command"]
            args = list(server.get("args", []))
            process = await asyncio.create_subprocess_exec(
                command,
                *args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(context.workspace),
            )
            assert process.stdin is not None and process.stdout is not None
            process.stdin.write(
                _frame(
                    {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {},
                            "clientInfo": {"name": "omega", "version": "0.1.0"},
                        },
                    }
                )
            )
            await process.stdin.drain()
            await _read_frame(process.stdout)
            process.stdin.write(_frame({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}))
            process.stdin.write(_frame({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}))
            await process.stdin.drain()
            response = await _read_frame(process.stdout)
            process.terminate()
            return PluginResult(plugin=self.name, action=action, ok=True, data=response.get("result", response))
        return self.unknown_action(action)
