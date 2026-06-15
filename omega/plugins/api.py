from __future__ import annotations

from typing import Any

import httpx

from omega.plugins.base import Plugin, PluginContext
from omega.schema import PluginResult


class APIPlugin(Plugin):
    name = "api"
    description = "Call REST and GraphQL APIs."
    actions = {
        "request": "Make an HTTP request.",
        "graphql": "Make a GraphQL request.",
    }

    async def call(self, action: str, arguments: dict[str, Any], context: PluginContext) -> PluginResult:
        if action == "request":
            async with httpx.AsyncClient(timeout=float(arguments.get("timeout", 30))) as client:
                response = await client.request(
                    method=str(arguments.get("method", "GET")).upper(),
                    url=str(arguments["url"]),
                    headers=arguments.get("headers"),
                    params=arguments.get("params"),
                    json=arguments.get("json"),
                    data=arguments.get("data"),
                )
            return PluginResult(
                plugin=self.name,
                action=action,
                ok=response.status_code < 400,
                data={"status_code": response.status_code, "headers": dict(response.headers), "text": response.text[:200000]},
                error=None if response.status_code < 400 else response.text[:1000],
            )
        if action == "graphql":
            async with httpx.AsyncClient(timeout=float(arguments.get("timeout", 30))) as client:
                response = await client.post(
                    str(arguments["url"]),
                    headers=arguments.get("headers"),
                    json={"query": arguments["query"], "variables": arguments.get("variables", {})},
                )
            return PluginResult(plugin=self.name, action=action, ok=response.status_code < 400, data=response.json())
        return self.unknown_action(action)
