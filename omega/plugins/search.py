from __future__ import annotations

import re
from html import unescape
from typing import Any
from urllib.parse import quote_plus

import httpx

from omega.plugins.base import Plugin, PluginContext
from omega.schema import PluginResult


class SearchPlugin(Plugin):
    name = "search"
    description = "Perform lightweight web search using DuckDuckGo HTML results."
    actions = {
        "web": "Search the public web.",
    }

    async def call(self, action: str, arguments: dict[str, Any], context: PluginContext) -> PluginResult:
        if action != "web":
            return self.unknown_action(action)
        query = str(arguments["query"])
        limit = int(arguments.get("limit", 5))
        url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            response = await client.get(url, headers={"User-Agent": "OMEGA/0.1"})
        if response.status_code >= 400:
            return PluginResult(plugin=self.name, action=action, ok=False, error=f"Search failed with {response.status_code}.")
        results = []
        for match in re.finditer(
            r'class="result__a" href="(?P<url>[^"]+)".*?>(?P<title>.*?)</a>.*?class="result__snippet"[^>]*>(?P<snippet>.*?)</a>',
            response.text,
            flags=re.DOTALL,
        ):
            title = re.sub(r"<.*?>", "", match.group("title"))
            snippet = re.sub(r"<.*?>", "", match.group("snippet"))
            results.append(
                {
                    "title": unescape(title).strip(),
                    "url": unescape(match.group("url")).strip(),
                    "snippet": unescape(snippet).strip(),
                }
            )
            if len(results) >= limit:
                break
        return PluginResult(plugin=self.name, action=action, ok=True, data=results)
